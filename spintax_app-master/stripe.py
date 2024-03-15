#! /usr/bin/env python3.6
"""
Python 3.6 or newer required.
"""
import json
import os
import stripe

# This is your test secret API key.
stripe.api_key = 'sk_test_51Meb9iSJwIaeMKmPEuYszdmeHFN7Hp8O2Wfrq0P27HsegqfHCD1K7UMP7RShARpR5BVVetF32eeHjY38VUbfH3mp00Y1VanN1F'




def create_payment():
    try:
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=1000,
            currency='inr',
            automatic_payment_methods={
                'enabled': True,
            },
        )
        print(intent)
    except Exception as e:
        print(e)


create_payment()
