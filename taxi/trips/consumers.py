from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from trips.serializers import NestedTripSerializer, TripSerializer
from trips.models import Trip


class TaxiConsumer(AsyncJsonWebsocketConsumer):
    groups = ['test']

    @database_sync_to_async
    def _get_user_group(self, user):
        return user.groups.first().name

    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            await self.close()
        else:
            user_group = await self._get_user_group(user)
            if user_group == 'driver':
                await self.channel_layer.group_add(
                    group='drivers',
                    channel=self.channel_name
                )

            for trip_id in await self._get_trip_ids(user):
                await self.channel_layer.group_add(
                    group=trip_id,
                    channel=self.channel_name
                )

            await self.accept()

    async def receive_json(self, content, **kwargs):
        message_type = content.get('type')
        if message_type == 'create.trip':
            await self.create_trip(content)
        elif message_type == 'echo.message':
            await self.echo_message(content)
        elif message_type == 'update.trip':
            await self.update_trip(content)

    async def create_trip(self, message):
        data = message.get('data')
        trip = await self._create_trip(data)
        trip_data = NestedTripSerializer(trip).data

        # Send rider requests to all drivers.
        await self.channel_layer.group_send(group='drivers', message={
            'type': 'echo.message',
            'data': trip_data
        })

        # Add rider to trip group.
        await self.channel_layer.group_add(  # new
            group=f'{trip.id}',
            channel=self.channel_name
        )

        await self.send_json({
            'type': 'echo.message',
            'data': trip_data,
        })

    # changed
    async def echo_message(self, message):
        await self.send_json(message)

    # new
    @database_sync_to_async
    def _create_trip(self, data):
        serializer = TripSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.create(serializer.validated_data)

    async def echo_message(self, message):
        await self.send_json(message)

    async def disconnect(self, code):
        user = self.scope['user']
        user_group = await self._get_user_group(user)
        if user_group == 'driver':
            await self.channel_layer.group_discard(
                group='drivers',
                channel=self.channel_name
            )

        # new
        for trip_id in await self._get_trip_ids(user):
            await self.channel_layer.group_discard(
                group=trip_id,
                channel=self.channel_name
            )

        await super().disconnect(code)

    @database_sync_to_async
    def _get_trip_ids(self, user):
        user_groups = user.groups.values_list('name', flat=True)
        if 'driver' in user_groups:
            trip_ids = user.trips_as_driver.exclude(
                status=Trip.COMPLETED
            ).only('id').values_list('id', flat=True)
        else:
            trip_ids = user.trips_as_rider.exclude(
                status=Trip.COMPLETED
            ).only('id').values_list('id', flat=True)
        return map(str, trip_ids)

    async def update_trip(self, message):
        # Get the trip data from the messsage sent by the driver
        data = message.get('data')
        # Call helper function to update the Trip object in the DB
        trip = await self._update_trip(data)
        # Get the trip.id from that object
        trip_id = f'{trip.id}'
        # Serialize the updated Trip data
        trip_data = NestedTripSerializer(trip).data

        # Server/consumer sends update to rider via the Trip group
        await self.channel_layer.group_send(
            group=trip_id,
            message={
                'type': 'echo.message',
                'data': trip_data
            }
        )

        await self.channel_layer.group_add(
            group=trip_id,
            channel=self.channel_name
        )

        await self.send_json({
            'type': 'echo.message',
            'data': trip_data
        })

    @database_sync_to_async
    def _update_trip(self, data):
        # Retrieve the Trip obj by ID
        instance = Trip.objects.get(id=data.get('id'))
        # Serialize the Trip data with update
        serializer = TripSerializer(data=data)
        # Ensure the serialized data is valid according to the model fields
        serializer.is_valid(raise_exception=True)
        # Use built-in update() passing in the Trip obj (instance) and the serializer data
        return serializer.update(instance, serializer.validated_data)
