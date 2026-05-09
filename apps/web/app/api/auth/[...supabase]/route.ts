import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({ message: "Supabase auth endpoint" });
}

export async function POST() {
  return NextResponse.json({ message: "Supabase auth endpoint" });
}
