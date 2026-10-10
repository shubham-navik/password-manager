import uuid

from locust import HttpUser, between, task


class PasswordManagerUser(HttpUser):
    wait_time = between(0.2, 0.8)

    def on_start(self):
        self.email = f"loadtest_{uuid.uuid4().hex}@example.com"
        self.password = "LoadTestPassword123!"
        self.vault_item_id = None
        self.authenticated = False

        self.register()
        self.login()

    def register(self):
        response = self.client.post(
            "/auth/register",
            json={
                "email": self.email,
                "password": self.password,
            },
            name="POST /auth/register",
        )

        if response.status_code != 201:
            print(
                f"Registration failed: "
                f"{response.status_code} {response.text}"
            )

    def login(self):
        response = self.client.post(
            "/auth/login",
            json={
                "email": self.email,
                "password": self.password,
            },
            name="POST /auth/login",
        )

        if response.status_code == 200:
            self.authenticated = True
        else:
            print(
                f"Login failed: "
                f"{response.status_code} {response.text}"
            )

    @task(5)
    def get_current_user(self):
        if not self.authenticated:
            return

        with self.client.get(
            "/auth/me",
            name="GET /auth/me",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Could not retrieve user: {response.status_code}"
                )

    @task(4)
    def list_vault_items(self):
        if not self.authenticated:
            return

        with self.client.get(
            "/api/v1/vault",
            name="GET /api/v1/vault",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Vault listing failed: {response.status_code}"
                )

    @task(3)
    def create_vault_item(self):
        if not self.authenticated:
            return

        payload = {
            "title": f"Load Test Item {uuid.uuid4().hex[:8]}",
            "website_url": "https://example.com",
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "password": "ExampleVaultPassword123!",
            "notes": "Created during an isolated load test",
        }

        with self.client.post(
            "/api/v1/vault",
            json=payload,
            name="POST /api/v1/vault",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 201):
                try:
                    data = response.json()
                    item_id = data.get("id")

                    if item_id:
                        self.vault_item_id = item_id
                    else:
                        response.failure(
                            "Vault creation succeeded but response "
                            "did not contain an id"
                        )
                except ValueError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(
                    f"Vault creation failed: {response.status_code}"
                )

    @task(4)
    def get_vault_item(self):
        if not self.authenticated or not self.vault_item_id:
            return

        with self.client.get(
            f"/api/v1/vault/{self.vault_item_id}",
            name="GET /api/v1/vault/{item_id}",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Vault retrieval failed: {response.status_code}"
                )

    @task(2)
    def update_vault_item(self):
        if not self.authenticated or not self.vault_item_id:
            return

        with self.client.patch(
            f"/api/v1/vault/{self.vault_item_id}",
            json={
                "title": f"Updated {uuid.uuid4().hex[:8]}",
            },
            name="PATCH /api/v1/vault/{item_id}",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Vault update failed: {response.status_code}"
                )

    @task(1)
    def delete_vault_item(self):
        if not self.authenticated or not self.vault_item_id:
            return

        item_id = self.vault_item_id

        with self.client.delete(
            f"/api/v1/vault/{item_id}",
            name="DELETE /api/v1/vault/{item_id}",
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 204):
                response.failure(
                    f"Vault deletion failed: {response.status_code}"
                )
            else:
                self.vault_item_id = None

    @task(1)
    def logout(self):
        if not self.authenticated:
            return

        response = self.client.post(
            "/auth/logout",
            name="POST /auth/logout",
        )

        if response.status_code == 204:
            self.authenticated = False