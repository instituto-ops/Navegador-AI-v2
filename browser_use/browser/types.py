import typing_extensions


class StorageStateOriginStorage(typing_extensions.TypedDict):
	name: str
	value: str


class StorageStateOrigin(typing_extensions.TypedDict):
	origin: str
	localStorage: typing_extensions.NotRequired[list[StorageStateOriginStorage]]
	sessionStorage: typing_extensions.NotRequired[list[StorageStateOriginStorage]]


class StorageStateCookie(typing_extensions.TypedDict):
	name: str
	value: str
	domain: str
	path: str
	expires: typing_extensions.NotRequired[float]
	httpOnly: typing_extensions.NotRequired[bool]
	secure: typing_extensions.NotRequired[bool]
	sameSite: typing_extensions.NotRequired[str]


class StorageState(typing_extensions.TypedDict):
	cookies: list[StorageStateCookie]
	origins: list[StorageStateOrigin]
