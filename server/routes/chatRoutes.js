const express = require("express");
const axios = require("axios");

const router = express.Router();

const GROQ_API_KEY = process.env.GROQ_API_KEY;

router.post("/", async (req, res) => {
  try {
    const { message, history } = req.body;

    if (!message) {
      return res.status(400).json({ error: "Message is required" });
    }

    const systemPrompt = `
You are CivicVoice Complaint Bot. You ONLY do one thing: collect details and generate a complaint.

STRICT RULES:
- You NEVER give advice, tips, steps, or general information.
- You NEVER ask the user what they want to do next.
- You NEVER say things like "Here is what you can do" or "You can contact...".
- You ONLY ask for missing details OR generate the complaint.
- You must be fully automatic. Do everything yourself.
- You must ALWAYS respond in EXACTLY one of the two formats below. No exceptions.

FLOW:
Step 1 — If the user describes a problem, check if you have ALL of these:
  - location (city or area)
  - what the problem is
  - how long it has been there OR how severe it is

Step 2 — If ANY detail is missing, respond ONLY in this exact format:

STATUS: NEED_INFO
QUESTIONS:
- [question about missing detail]

Step 3 — Once you have location + problem + any severity info, respond ONLY in this exact format:

STATUS: READY

COMPLAINT:
[Write a formal 80-100 word complaint addressed to the relevant municipal authority. Include location, problem description, duration/severity, and request for urgent action.]

CATEGORY:
[one of: Road & Infrastructure / Water & Sanitation / Environment / Public Safety / Health / Education]

URGENCY:
[Low / Medium / High]

QUALITY:
[a number from 60 to 100]

CRITICAL: Never write anything outside these two formats. No greetings. No explanations. No advice. Just the format.
`;

    const conversationMessages = [
      { role: "system", content: systemPrompt },
    ];

    if (history && Array.isArray(history)) {
      history.forEach((msg) => {
        conversationMessages.push({
          role: msg.sender === "user" ? "user" : "assistant",
          content: msg.text,
        });
      });
    }

    conversationMessages.push({
      role: "user",
      content: message,
    });

    const response = await axios.post(
      "https://api.groq.com/openai/v1/chat/completions",
      {
        model: "llama-3.3-70b-versatile",
        messages: conversationMessages,
        temperature: 0.2,
        max_tokens: 500,
      },
      {
        headers: {
          Authorization: `Bearer ${GROQ_API_KEY}`,
          "Content-Type": "application/json",
        },
      }
    );

    console.log("✅ Groq response received");

    let reply = response.data.choices[0].message.content;
    reply = reply
      .replace(/<\/assistant>/g, "")
      .replace(/<assistant>/g, "")
      .trim();

    res.json({ reply });

  } catch (err) {
    console.log("Status:", err.response?.status);
    console.log("Error:", JSON.stringify(err.response?.data, null, 2));

    res.status(500).json({
      error: err.response?.data?.error?.message || "Chatbot error",
    });
  }
});

module.exports = router;