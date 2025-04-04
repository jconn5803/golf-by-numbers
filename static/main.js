

// Initialize Stripe with the publishable key retrieved from /config
fetch("/config")
  .then((result) => result.json())
  .then((data) => {
    const stripe = Stripe(data.publicKey);

    // Event listener for the monthly subscription button
    document.querySelector("#monthlyBtn").addEventListener("click", () => {
      fetch("/create-checkout-session?product_type=monthly")
        .then((result) => result.json())
        .then((data) => stripe.redirectToCheckout({ sessionId: data.sessionId }))
        .then((res) => {
          console.log(res);
        });
    });

    // Event listener for the annual subscription button
    document.querySelector("#annualBtn").addEventListener("click", () => {
      fetch("/create-checkout-session?product_type=annual")
        .then((result) => result.json())
        .then((data) => stripe.redirectToCheckout({ sessionId: data.sessionId }))
        .then((res) => {
          console.log(res);
        });
    });
  });