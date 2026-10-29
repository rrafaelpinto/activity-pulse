import tempfile
from io import StringIO
from pathlib import Path

import yaml
from django.core.management import call_command
from rest_framework.test import APIClient, APITestCase

HTTP_METHODS = {"get", "put", "post", "patch", "delete", "options", "head", "trace"}


class OpenApiSchemaTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.schema = APIClient().get("/api/schema/?format=json").json()

    def test_schema_is_valid_without_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "schema.yml"
            call_command("spectacular", "--validate", "--fail-on-warn", "--file", str(target), stderr=StringIO())
            self.assertEqual(yaml.safe_load(target.read_text())["openapi"][:1], "3")

    def test_only_the_two_read_only_endpoints_are_documented(self):
        self.assertEqual(
            set(self.schema["paths"]), {"/api/accounts/", "/api/accounts/{account_id}/activity/"}
        )
        for path, operations in self.schema["paths"].items():
            self.assertEqual(set(operations) & HTTP_METHODS, {"get"}, path)

    def test_no_authentication_is_declared(self):
        self.assertNotIn("securitySchemes", self.schema.get("components", {}))
        for operations in self.schema["paths"].values():
            self.assertNotIn("security", operations["get"])

    def test_activity_endpoint_documents_as_of_and_the_error_responses(self):
        operation = self.schema["paths"]["/api/accounts/{account_id}/activity/"]["get"]
        parameters = {p["name"]: p for p in operation["parameters"]}
        self.assertEqual(parameters["as_of"]["schema"], {"type": "string", "format": "date"})
        self.assertFalse(parameters["as_of"].get("required", False))
        self.assertTrue(parameters["account_id"]["required"])
        self.assertEqual(set(operation["responses"]), {"200", "400", "404"})

    def test_headline_is_numbers_only_and_locations_have_a_status_enum(self):
        schemas = self.schema["components"]["schemas"]
        self.assertEqual(set(schemas["Headline"]["properties"]), {"this_week", "usual", "delta_pct"})
        self.assertEqual(
            schemas["StatusEnum"]["enum"], ["below", "normal", "above", "not_enough_data"]
        )
        self.assertIn("status", schemas["LocationActivity"]["properties"])
        for nullable in ("usual", "delta_pct"):
            self.assertTrue(schemas["Headline"]["properties"][nullable]["nullable"])

    def test_swagger_ui_page_is_served_and_points_at_the_schema(self):
        response = self.client.get("/api/docs/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response["Content-Type"])
        html = response.content.decode()
        self.assertIn("/api/schema/", html)
        self.assertIn("swagger-ui-dist@5.17.14", html)  # pinned version, not "latest"

    def test_schema_endpoint_serves_yaml_and_json(self):
        self.assertEqual(self.client.get("/api/schema/").status_code, 200)
        self.assertEqual(self.client.get("/api/schema/?format=json")["Content-Type"], "application/vnd.oai.openapi+json")
