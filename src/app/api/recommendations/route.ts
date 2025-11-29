// src/app/api/recommendations/route.ts
import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

export const runtime = "nodejs"

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const city = searchParams.get("city") ?? ""
    const query = searchParams.get("query") ?? ""
    const pages = parseInt(searchParams.get("pages") ?? "2", 10)

    if (!city || !query) {
      return NextResponse.json(
        { error: "city and query parameters required" },
        { status: 400 }
      )
    }

    console.log(`📨 Recommendation search: city=${city}, query=${query}, pages=${pages}`)

    // Forward to recommendation backend
    const backendUrl = process.env.RECOMMENDATION_BACKEND_URL ?? "http://localhost:8001/search"
    const url = new URL(backendUrl)
    url.searchParams.set("city", city)
    url.searchParams.set("query", query)
    url.searchParams.set("pages", String(pages))

    try {
      const res = await fetch(url.toString(), { method: "GET" })

      if (res.ok) {
        const json = await res.json()
        console.log(`➡️ Recommendation backend returned ${(json as Array<unknown>).length || 0} results`)
        return NextResponse.json(json)
      }

      console.warn(`⚠️ Backend status=${res.status}, returning empty list`)
      return NextResponse.json([])
    } catch (err) {
      console.warn("⚠️ Could not reach recommendation backend:", err)
      // Return mock recommendations
      return NextResponse.json([
        {
          id: "mock-1",
          name: "Dr. Rajesh Kumar",
          specialization: "Neurology",
          experience: 15,
          rating: 92,
          reviews: 248,
          fees: 1200,
          hospital: "City Medical Center",
          locality: "Downtown",
          lat: null,
          lon: null,
          image: "https://via.placeholder.com/70",
          profile_link: "#",
          score: 92 + (15 * 1.5) + (248 ** 0.5 * 5)
        }
      ])
    }
  } catch (err) {
    console.error("❌ Recommendations error:", err)
    return NextResponse.json({ error: "Server error" }, { status: 500 })
  }
}
