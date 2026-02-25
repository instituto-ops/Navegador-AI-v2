from typing import TypedDict, List, NotRequired

class StorageStateOriginStorage(TypedDict):
	name: str
	value: str

class StorageStateOrigin(TypedDict):
	origin: str
	localStorage: NotRequired[List[StorageStateOriginStorage]]
	sessionStorage: NotRequired[List[StorageStateOriginStorage]]

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
	cookies: List[StorageStateCookie]
	origins: List[StorageStateOrigin]
