import serpapi

client = serpapi.Client(api_key="74dfaaa8c7d60ea26735bc24abe91146f34b58d4c3359052053ce34c763439b4")
results = client.search({
  "engine": "google_flights",
  "departure_id": "CDG",
  "arrival_id": "AUS",
  "currency": "USD",
  "type": "2",
  "outbound_date": "2026-06-01"
})
best_flights = results["best_flights"]