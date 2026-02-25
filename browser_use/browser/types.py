from typing import NotRequired, TypedDict


class StorageStateOriginStorage(TypedDict):
	name: str
	value: str


class StorageStateOrigin(TypedDict):
	origin: str
	localStorage: NotRequired[list[StorageStateOriginStorage]]
	sessionStorage: NotRequired[list[StorageStateOriginStorage]]


class StorageStateCookie(TypedDict):
	name: str
	value: str
	domain: str
	path: str
	expires: NotRequired[float]
	httpOnly: NotRequired[bool]
	secure: NotRequired[bool]
	sameSite: NotRequired[str]


class StorageState(TypedDict):
	cookies: list[StorageStateCookie]
	origins: list[StorageStateOrigin]
