row_data = {
    "city": "Salt Lake City",
    "country": "US"
}

city = row_data.get("city")
country = row_data.get("country")

row_data["location"] = " ".join(filter(None, [city, country]))

print(row_data)