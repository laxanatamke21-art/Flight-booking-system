import braintree

BRAINTREE_MERCHANT_ID = "8xbqdmkdzvy4q995"

BRAINTREE_PUBLIC_KEY = "qghj3vgkn5rpjt6m"

BRAINTREE_PRIVATE_KEY = "d422b6b528f022da66b4d9bc8739590f"

gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        environment=braintree.Environment.Sandbox,
        merchant_id=BRAINTREE_MERCHANT_ID,
        public_key=BRAINTREE_PUBLIC_KEY,
        private_key=BRAINTREE_PRIVATE_KEY
    )
)

print("✅ Braintree Sandbox Gateway initialized")