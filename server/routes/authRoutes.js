const express = require("express");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const User = require("../models/User");

const router = express.Router();

const SECRET = process.env.JWT_SECRET;

// REGISTER
router.post("/register", async (req, res) => {
  const { name, ngo_name, email, password, role, ngo_category } = req.body;

  const hashed = await bcrypt.hash(password, 10);

  const user = new User({
    name,
    ngo_name,
    email,
    password: hashed,
    role,
    ngo_category,
  });

  await user.save();

  res.json({
    message: "User registered",
  });
});

// LOGIN
router.post("/login", async (req, res) => {
  try {
    const { email, password } = req.body;

    const user = await User.findOne({ email });

    if (!user) {
      return res.status(400).json({
        error: "User not found",
      });
    }

    const valid = await bcrypt.compare(password, user.password);

    if (!valid) {
      return res.status(400).json({
        error: "Wrong password",
      });
    }

    const token = jwt.sign(
      {
        id: user._id,
        role: user.role,
        ngo_category: user.ngo_category,
        name: user.name,
        ngo_name: user.ngo_name,
        city: user.city,
        district: user.district,
        state: user.state,
      },
      SECRET,
    );

    res.json({
      token,
      user: {
        id: user._id,
        name: user.name,
        ngo_name: user.ngo_name,
        role: user.role,
        ngo_category: user.ngo_category,
      },
    });
  } catch (err) {
    res.status(500).json({
      error: err.message,
    });
  }
});

module.exports = router;
