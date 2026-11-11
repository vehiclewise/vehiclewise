from vehicles import vehicles


def get_recommendations():
    print("\n========== VEHICLE RECOMMENDATION SYSTEM ==========\n")

    # Get user preferences
    budget = input("Enter your maximum budget (press Enter to skip): ")

    fuel = input(
        "Preferred fuel type (Petrol/ Diesel/ Hybrid/ Electric): "
    ).strip()

    vehicle_type = input(
        "Preferred vehicle type (SUV/ Sedan/ Hatchback/ Estate): "
    ).strip()

    transmission = input(
        "Preferred transmission (Automatic/ Manual): "
    ).strip()

    min_power = input("Minimum horsepower (press Enter to skip): ")

    # Convert numeric inputs
    budget = float(budget) if budget else None
    min_power = int(min_power) if min_power else None

    recommendations = []

    for vehicle in vehicles:

        score = 0

        # Preference filters
        if budget is not None and vehicle["price"] > budget:
            continue

        if fuel and vehicle["fuel_type"].lower() != fuel.lower():
            continue

        if vehicle_type and vehicle["vehicle_type"].lower() != vehicle_type.lower():
            continue

        if transmission and vehicle["transmission"].lower() != transmission.lower():
            continue

        if min_power is not None and vehicle["power_hp"] < min_power:
            continue

        # Recommendation scoring
        score += 40

        # Higher horsepower gets additional points
        score += min(vehicle["power_hp"] / 300 * 20, 20)

        # More seats get additional points
        score += min(vehicle["seats"] / 7 * 20, 20)

        # Lower-priced vehicles get additional points
        score += max(0, 20 - (vehicle["price"] / 50000 * 20))

        recommendations.append((vehicle, round(score, 2)))

    # Sort recommendations by score
    recommendations.sort(key=lambda x: x[1], reverse=True)

    # Display results
    print("\n========== RECOMMENDED VEHICLES ==========\n")

    if not recommendations:
        print("No vehicles match your preferences.")
        return

    for rank, (vehicle, score) in enumerate(recommendations, 1):

        print(f"\nRank: {rank}")
        print(f"Vehicle: {vehicle['brand']} {vehicle['model']}")
        print(f"Price: ${vehicle['price']}")
        print(f"Fuel: {vehicle['fuel_type']}")
        print(f"Vehicle Type: {vehicle['vehicle_type']}")
        print(f"Transmission: {vehicle['transmission']}")
        print(f"Power: {vehicle['power_hp']} HP")
        print(f"Seats: {vehicle['seats']}")
        print(f"Recommendation Score: {score}/100")


if __name__ == "__main__":
    get_recommendations()
