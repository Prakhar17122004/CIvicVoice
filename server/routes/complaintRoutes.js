const express = require("express");
const axios = require("axios");
const router = express.Router();
const Complaint = require("../models/Complaint");
const auth = require("../middleware/authMiddleware");

// Creating Complaint or issue
router.post("/predict", auth, async (req, res) => {
  try {
    const { text, city } = req.body;

    const response = await axios.post( `${process.env.FLASK_API_URL}/predict`, {
      text,
      city,
    });

    const result = response.data;

    const complaint = new Complaint({
  text,
  city,
  ngo_category: result.ngo_category,
  urgency: result.urgency,

  reason: result.reason,

  ngo_details: result.ngo_details,

  user_id: req.user.id,
});

    await complaint.save();

    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});


router.get("/my-complaints", auth, async (req, res) => {
  const complaints = await Complaint.find({ user_id: req.user.id });
  res.json(complaints);
});


router.get("/ngo-complaints", auth, async (req, res) => {
  const complaints = await Complaint.find({
    ngo_category: req.user.ngo_category,
  });

  res.json(complaints);
});

module.exports = router;
