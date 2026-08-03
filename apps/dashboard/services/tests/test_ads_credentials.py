"""Round-trip encryption + masking for Ads platform credentials. ProjectSettings
persistence (get_decrypted_credential/record_test_result against a real row) is covered
in test_settings_service.py alongside the rest of the settings save/read path."""
from django.test import TestCase

from apps.dashboard.services.ads_credentials import encrypt_fields, decrypt_fields, mask


class EncryptDecryptTests(TestCase):
    def test_round_trips_a_field_dict(self):
        original = {"developer_token": "abc123", "customer_id": "1234567890"}
        token = encrypt_fields(original)
        self.assertNotIn("abc123", token)  # never stored in the clear
        self.assertEqual(decrypt_fields(token), original)


class MaskTests(TestCase):
    def test_masks_all_but_last_four_characters(self):
        self.assertEqual(mask("abcdefgh1234"), "••••1234")

    def test_short_value_masks_completely(self):
        self.assertEqual(mask("abc"), "•••")

    def test_blank_value_masks_to_empty(self):
        self.assertEqual(mask(""), "")
