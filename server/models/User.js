const mongoose = require("mongoose");

const userSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: true,
    },

    email: {
      type: String,
      required: true,
      unique: true,
    },

    password: {
      type: String,
      required: true,
    },

    role: {
      type: String,
      enum: ["volunteer", "ngo"],
      default: "volunteer",
    },

    // NGO DETAILS
    ngo_name: {
      type: String,
    },

    ngo_category: {
      type: String,
    },

    city: {
      type: String,
    },

    district: {
      type: String,
    },

    state: {
      type: String,
    },

    vacancy: {
      type: String,
      default: "NA",
    },
  },
  { timestamps: true },
);

module.exports = mongoose.model("User", userSchema);
