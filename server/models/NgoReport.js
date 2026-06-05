const mongoose = require("mongoose");

const ngoReportSchema = new mongoose.Schema(
  {
    ngoName: {
      type: String,
      required: true,
    },

    complaintType: {
      type: String,
      required: true,
    },

    description: {
      type: String,
      required: true,
    },

    city: {
      type: String,
      required: true,
    },

    severity: {
      type: String,
      default: "Medium",
    },

    status: {
      type: String,
      default: "Pending",
    },

    reportedBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
    },
  },
  {
    timestamps: true,
  },
);

module.exports = mongoose.model("NgoReport", ngoReportSchema);
