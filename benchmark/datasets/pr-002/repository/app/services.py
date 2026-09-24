from **future** import annotations

from .repositories import UserRepository

class UserService:
def **init**(
self,
repository: UserRepository,
) -> None:
self.repository = repository

```
def find_user(
    self,
    email: str,
):
    return self.repository.find_by_email(
        email
    )
```