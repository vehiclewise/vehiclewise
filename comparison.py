from vehicles import vehicles


def compare_vehicles(vehicle_ids):
    """Compare 2 or 3 vehicles using their technical specifications."""

    if not 2 <= len(vehicle_ids) <= 3:
        print("Please select 2 or 3 vehicles.")
        return

    selected = [
        vehicle for vehicle in vehicles
        if vehicle["id"] in vehicle_ids
    ]

    if len(selected) != len(vehicle_ids):
        print("Invalid vehicle ID.")
        return

    specifications = [
        "brand",
        "model",
        "price",
        "fuel_type",
        "vehicle_type",
        "transmission",
        "power_hp",
        "seats"
    ]

    print("\n========== VEHICLE COMPARISON ==========\n")

    print(f"{'Specification':<20}", end="")

    for vehicle in selected:
        name = f"{vehicle['brand']} {vehicle['model']}"
        print(f"{name:<22}", end="")

    print("\n" + "-" * 85)

    for spec in specifications:
        print(f"{spec:<20}", end="")

        for vehicle in selected:
            print(f"{str(vehicle.get(spec, 'N/A')):<22}", end="")

        print()

    cheapest = min(selected, key=lambda v: v["price"])
    powerful = max(selected, key=lambda v: v["power_hp"])

    print("\n========== COMPARISON RESULTS ==========")

    print(
        f"Cheapest vehicle: "
        f"{cheapest['brand']} {cheapest['model']}"
    )

    print(
        f"Most powerful vehicle: "
        f"{powerful['brand']} {powerful['model']}"
    )


if __name__ == "__main__":

    print("Available Vehicles:")

    for vehicle in vehicles:
        print(
            f"{vehicle['id']}. "
            f"{vehicle['brand']} {vehicle['model']}"
        )

    ids = input(
        "\nEnter 2 or 3 vehicle IDs separated by commas: "
    )

    try:
        vehicle_ids = [
            int(value.strip())
            for value in ids.split(",")
        ]

        compare_vehicles(vehicle_ids)

    except ValueError:
        print("Please enter valid numeric IDs.")
