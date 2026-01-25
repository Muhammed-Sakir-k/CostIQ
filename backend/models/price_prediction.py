import numpy as np
from sklearn.linear_model import LinearRegression

def predict_trend(price_history):
    """
    Takes list of past prices
    Returns: 'UP' or 'DOWN'
    """

    # Prepare data
    X = np.array(range(len(price_history))).reshape(-1, 1)
    y = np.array(price_history)

    # Train model
    model = LinearRegression()
    model.fit(X, y)

    # Predict next price
    next_day = np.array([[len(price_history)]])
    predicted_price = model.predict(next_day)[0]

    current_price = price_history[-1]

    if predicted_price > current_price:
        return "UP"
    else:
        return "DOWN"
