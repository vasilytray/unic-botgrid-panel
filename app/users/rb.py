class RBUser:
    def __init__(self, user_id: int | None = None,
                 user_status: int | None = None,
                 role_id: int | None = None,
                 email_verified: int | None = None,):
        self.id = user_id
        self.user_status = user_status
        self.role_id = role_id
        self.email_verified = email_verified

        
    def to_dict(self) -> dict:
        data = {'id': self.id, 'user_status': self.user_status, 'role_id': self.role_id,
                "email_verified": self.email_verified}
        # Создаем копию словаря, чтобы избежать изменения словаря во время итерации
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data