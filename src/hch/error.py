class BaseHunterError(Exception):
    def __init__(self, message: str = "") -> None:
        super().__init__(message)


class LoadCourseError(BaseHunterError):
    pass


class HuntCourseError(BaseHunterError):
    pass


class CookieExpiredError(BaseHunterError):
    pass


class GetCookieError(BaseHunterError):
    pass


class GetCourseCategoryError(BaseHunterError):
    pass


class GetCourseError(BaseHunterError):
    pass


class MaxRetriesError(BaseHunterError):
    pass


class GetTimeInfoError(BaseHunterError):
    pass


class GetHuntedCourseError(BaseHunterError):
    pass


class GetGradeError(BaseHunterError):
    pass
