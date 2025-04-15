const { Auth, LoginCredentials } = require("two-step-auth");

async function sendOtp(emailId) {
  try {
    const res = await Auth(emailId, "YourCompanyName");
    console.log("OTP sent:", res);
    return res;
  } catch (error) {
    console.error("Error sending OTP:", error);
    throw error;
  }
}

// Example usage: send OTP to a test email
// sendOtp("test@example.com");

module.exports = { sendOtp, LoginCredentials };
