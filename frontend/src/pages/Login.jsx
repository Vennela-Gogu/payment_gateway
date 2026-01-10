import React from "react";
import { useNavigate } from "react-router-dom";

const Login = () => {
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    // For simplicity, assume login is always successful
    navigate("/dashboard");
  };

  return (
    <form data-test-id="login-form" onSubmit={handleLogin} style={{ textAlign: "center", marginTop: "50px" }}>
      <h2>Login</h2>
      <input data-test-id="email-input" type="email" placeholder="Email" /><br /><br />
      <input data-test-id="password-input" type="password" placeholder="Password" /><br /><br />
      <button data-test-id="login-button" type="submit">Login</button>
    </form>
  );
};

export default Login;