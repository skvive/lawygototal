package site.lexid.lawygo

/** Screen routes are native Compose destinations; none is a full-page WebView. */
enum class Product(val label: String, val subtitle: String, val endpoint: String) {
    HOME("홈", "법률 인텔리전스", ""),
    JOURNAL("저널", "국내·미국 경제 인사이트", "/api/journal/news"),
    CHANNEL("채널", "전문가 콘텐츠", "/api/posts?product=channel"),
    PAN("판", "법률 전문가의 콘텐츠", "/api/growth/feed"),
    WIKI("위키", "검증된 법률정보 검색", "/api/wiki/search"),
    NOTE("노트", "비공개 법률 노트", "/api/posts?product=note"),
    PRO("프로", "송무 관리", "/api/hub/modules"),
    HUB("관리", "모듈 운영 허브", "/api/hub/overview")
}

/** Contracts copied from the LAWYGO 6.1 FastAPI backend and isolated for QA. */
object ApiPaths {
    const val LOGIN = "/api/auth/login"
    const val LOGOUT = "/api/auth/logout"
    const val ME = "/api/me"
    const val POSTS = "/api/posts"
    const val BOARDS = "/api/boards"
    const val JOURNAL = "/api/journal/news"
    const val WIKI = "/api/wiki/search"
    const val PAN = "/api/growth/feed"
    const val NOTE_EXTRACT = "/api/note/"
    const val NOTE_AI = "/api/note/"
    const val HUB = "/api/hub/overview"
    const val METRICS = "/api/dashboard/stats"
}
