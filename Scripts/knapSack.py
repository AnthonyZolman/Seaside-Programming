def knapsack_01(weights, values, capacity):
    n = len(weights)
    # Create a 2D DP table initialized with 0s
    # Rows: items (0 to n), Columns: capacity (0 to capacity)
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]

    # Build the table bottom-up
    for i in range(1, n + 1):
        for w in range(1, capacity + 1):
            # Check if the weight of the current item fits in the current capacity
            if weights[i-1] <= w:
                # Max of:
                # 1. Including the item (value + best value of remaining capacity)
                # 2. Excluding the item (best value from the row above)
                dp[i][w] = max(values[i-1] + dp[i-1][w - weights[i-1]],
                               dp[i-1][w])
            else:
                # If it doesn't fit, carry over the value from the row above
                dp[i][w] = dp[i-1][w]

    return dp[n][capacity]

# Data from our example
item_weights = [1, 3, 4, 5]
item_values = [1, 4, 5, 7]
knapsack_capacity = 7

result = knapsack_01(item_weights, item_values, knapsack_capacity)
print(f"The maximum value that can be carried is: ${result}")