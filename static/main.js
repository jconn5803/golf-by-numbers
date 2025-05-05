// Initialize Stripe with the publishable key retrieved from /config
fetch("/config")
  .then(r => r.json())
  .then(({ publicKey }) => {
    const stripe = Stripe(publicKey);

    // FREE plan button
    document.querySelector("#freeBtn").addEventListener("click", () => {
      if (!isAuthenticated) {
        window.location.href = "/register";
      } else {
        // logged in, whether active or not, free users go straight to dashboard
        window.location.href = "/dashboard";
      }
    });

    // PRO MONTHLY button
    document.querySelector("#monthlyBtn").addEventListener("click", () => {
      if (!isAuthenticated) {
        return window.location.href = "/register";
      }
      if (subscriptionActive) {
        return window.location.href = "/dashboard";
      }
      // not subscribed yet: kick off Stripe checkout
      fetch("/create-checkout-session?product_type=monthly")
        .then(r => r.json())
        .then(data => stripe.redirectToCheckout({ sessionId: data.sessionId }))
        .catch(console.error);
    });
    
    // PRO Release button
    document.querySelector("#releaseBtn").addEventListener("click", () => {
      if (!isAuthenticated) {
        return window.location.href = "/register";
      }
      if (subscriptionActive) {
        return window.location.href = "/dashboard";
      }
      // not subscribed yet: kick off Stripe checkout
      fetch("/create-checkout-session?product_type=release")
        .then(r => r.json())
        .then(data => stripe.redirectToCheckout({ sessionId: data.sessionId }))
        .catch(console.error);
    });

    // PRO YEARLY button
    document.querySelector("#annualBtn").addEventListener("click", () => {
      if (!isAuthenticated) {
        return window.location.href = "/register";
      }
      if (subscriptionActive) {
        return window.location.href = "/dashboard";
      }
      fetch("/create-checkout-session?product_type=annual")
        .then(r => r.json())
        .then(data => stripe.redirectToCheckout({ sessionId: data.sessionId }))
        .catch(console.error);
    });

    // (If you ever add a daily plan button, do the same pattern.)
  });