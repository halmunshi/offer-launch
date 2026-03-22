import { verifyWebhook } from "@clerk/nextjs/webhooks";
import { NextResponse, NextRequest } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const CLERK_WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET;

export async function POST(req: NextRequest) {
  if (!CLERK_WEBHOOK_SECRET) {
    return NextResponse.json(
      { error: "CLERK_WEBHOOK_SECRET is not set" },
      { status: 500 },
    );
  }

  if (!API_URL) {
    return NextResponse.json(
      { error: "NEXT_PUBLIC_API_URL is not set" },
      { status: 500 },
    );
  }

  try {
    const event = await verifyWebhook(req, {
      signingSecret: CLERK_WEBHOOK_SECRET,
    });

    if (event.type === "user.created") {
      const forwardResponse = await fetch(`${API_URL}/webhooks/clerk`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(event),
      });

      if (!forwardResponse.ok) {
        const errorBody = await forwardResponse.text();
        throw new Error(errorBody || "Failed to forward Clerk webhook");
      }
    }

    return NextResponse.json({ ok: true }, { status: 200 });
  } catch {
    return NextResponse.json({ error: "Invalid webhook signature" }, { status: 400 });
  }
}
