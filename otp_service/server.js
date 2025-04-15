const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const { Auth } = require('two-step-auth');

const app = express();
const port = 3001;

app.use(cors());
app.use(bodyParser.json());

app.post('/send-otp', async (req, res) => {
  const { email, companyName } = req.body;
  if (!email) {
    return res.status(400).json({ error: 'Email is required' });
  }
  try {
    const result = await Auth(email, companyName || 'YourCompanyName');
    res.json({ success: result.success, mail: result.mail, OTP: result.OTP });
  } catch (error) {
    console.error('Error sending OTP:', error);
    res.status(500).json({ error: 'Failed to send OTP' });
  }
});

app.listen(port, () => {
  console.log(`OTP service listening at http://localhost:${port}`);
});
