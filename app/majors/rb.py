class RBMajor:
    def __init__(self, major_id: int | None = None,
                 major_name: str | None = None,
                 major_description: int | None = None,):
        self.major_id = major_id
        self.major_name = major_name
        self.major_description = major_description
        
    def to_dict(self) -> dict:
        data = {'id': self.major_id, 'major_name': self.major_name, 'major_description': self.major_description}
        # Создаем копию словаря, чтобы избежать изменения словаря во время итерации
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data