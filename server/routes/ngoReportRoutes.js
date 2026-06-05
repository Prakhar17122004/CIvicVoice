const express = require("express");
const router = express.Router();

const NgoReport = require("../models/NgoReport");
const auth = require("../middleware/authMiddleware");

// CREATE REPORT
router.post("/", auth, async (req, res) => {
  try {
    const report = new NgoReport({
      ...req.body,
      ngoName: req.body.ngoName.trim().toLowerCase(),
      reportedBy: req.user.id,
    });

    await report.save();

    res.status(201).json({
      success: true,
      report,
    });
  } catch (err) {
    res.status(500).json({
      success: false,
      message: err.message,
    });
  }
});

// GET ALL REPORTS
router.get("/", async (req, res) => {
  try {
    const reports = await NgoReport.find().sort({
      createdAt: -1,
    });

    res.json(reports);
  } catch (err) {
    res.status(500).json({
      message: err.message,
    });
  }
});

module.exports = router;
