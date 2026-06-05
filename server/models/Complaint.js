const mongoose = require("mongoose");

const ComplaintSchema = new mongoose.Schema({
  text: String,

  city: String,

  ngo_category: String,

  urgency: String,

  reason: String,

  ngo_details: Object,

  user_id: String,

  createdAt: {
    type: Date,
    default: Date.now,
  },

  target_ngo: {
    type: String,
  },
});

module.exports = mongoose.model("Complaint", ComplaintSchema);