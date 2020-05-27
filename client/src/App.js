import React, { useState } from "react";
import { Container, Navbar, Button, Form } from "react-bootstrap";
import { LinkContainer } from "react-router-bootstrap";
import { Route, Link, Switch, Redirect } from "react-router-dom";
import LogIn from "./components/LogIn";
import SignUp from "./components/SignUp";

import "./App.css";
import axios from "axios";

export const App = (props) => {
  const [isLoggedIn, setLoggedIn] = useState(() => {
    return window.localStorage.getItem("taxi.auth") !== null;
  });

  // logIn sends credentials to the server and sets the localStorage; it returns response (with errors if necessary)
  const logIn = async (username, password) => {
    const url = "/api/log_in/";
    try {
      const response = await axios.post(url, { username, password });
      window.localStorage.setItem("taxi.auth", JSON.stringify(response.data));
      setLoggedIn(true);
      return { response, isError: false };
    } catch (error) {
      console.error(error);
      return { response: error, isError: true };
    }
  };

  const logOut = () => {
    window.localStorage.removeItem("taxi.auth");
    setLoggedIn(false);
  };

  return (
    <>
      <Navbar bg='light' expand='lg' variant='light'>
        <LinkContainer to='/'>
          <Navbar.Brand className='logo'>Taxi</Navbar.Brand>
        </LinkContainer>
        <Navbar.Toggle />
        <Navbar.Collapse>
          {isLoggedIn && (
            <Form inline className='ml-auto'>
              <Button type='button' onClick={() => logOut()}>
                Log out
              </Button>
            </Form>
          )}
        </Navbar.Collapse>
      </Navbar>
      <Container className='pt-3'>
        <Switch>
          <Route
            exact
            path='/'
            render={() => (
              <div className='middle-center'>
                <h1 className='landing logo'>Taxi</h1>
                {!isLoggedIn && (
                  <Link id='signUp' className='btn btn-primary' to='/sign-up'>
                    Sign up
                  </Link>
                )}
                {!isLoggedIn && (
                  <Link id='logIn' className='btn btn-primary' to='/log-in'>
                    Log in
                  </Link>
                )}
              </div>
            )}
          />
          <Route
            path='/sign-up'
            render={() => (isLoggedIn ? <Redirect to='/' /> : <SignUp />)}
          />
          <Route
            path='/log-in'
            render={() =>
              // If loggedIn true, then redirect to home page if not then direct/render to Log In page where props.logIn can make API call through LogIn component
              isLoggedIn ? <Redirect to='/' /> : <LogIn logIn={logIn} />
            }
          />{" "}
        </Switch>
      </Container>
    </>
  );
};

export default App;
