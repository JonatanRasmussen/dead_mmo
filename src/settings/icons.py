

class Icons:
    PORO = "Poro"

    @staticmethod
    def get_icon_name(icon_id: int) -> str:
        if icon_id == 24020:
            return Icons.PORO
        return ""