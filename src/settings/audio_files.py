

class AudioFiles:
    """ Audio file names """
    REJUVENATION_APPLY = "Rejuvenation"
    SHADOW_BOLT_BUILD = "ShadowBoltBuild"
    SHADOW_BOLT_CAST = "ShadowBoltCast"
    SHADOW_BOLT_HIT = "ShadowBoltHit"

    @staticmethod
    def get_audio_name(icon_id: int) -> str:
        if icon_id == 16800:
            return AudioFiles.REJUVENATION_APPLY
        elif icon_id == 16801:
            return AudioFiles.SHADOW_BOLT_BUILD
        elif icon_id == 16802:
            return AudioFiles.SHADOW_BOLT_CAST
        elif icon_id == 16803:
            return AudioFiles.SHADOW_BOLT_HIT
        return ""