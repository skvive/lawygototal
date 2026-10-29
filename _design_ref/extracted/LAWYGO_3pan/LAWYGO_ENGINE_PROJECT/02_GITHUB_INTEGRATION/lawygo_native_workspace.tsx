/** Drop into src/app/workspace/products/page.tsx in shinkangteam/lawygo.
 * Runs in the EXISTING LAWYGO Next.js session/Supabase tenant, without a second login.
 * Note points to private native legal notebook, not the public boards.
 */
import Link from 'next/link';
import { getSession } from '@/lib/authSession';
import { getTenantManagementNumber } from '@/lib/boardApiContext';
import { listBoards } from '@/lib/boardService';

const modules = [
  {slug:'channel',label:'LAWYGO CHANNEL',name:'로이고 채널',board:'lawygo_channel',desc:'법률·경제 뉴스와 전문 콘텐츠',icon:'▤'},
  {slug:'wiki',label:'LAWYGO WIKI',name:'로이고 위키',board:'lawygo_wiki',desc:'판례·법령과 온라인 법률 백과사전',icon:'▦'},
  {slug:'pan',label:'LAWYGO PAN',name:'로이고 판',board:'lawygo_pan',desc:'변호사 브랜드·블로그·영상 게시판',icon:'◈'},
  {slug:'note',label:'LAWYGO NOTE',name:'로이고 노트',board:null,desc:'비공개 법률 노트·판례·업로드 문서 분석',icon:'✎'},
] as const;

export default async function ProductWorkspace() {
  const session = await getSession();
  if (!session) return <main className="min-h-screen bg-slate-50 p-12"><h1 className="text-2xl font-bold">LAWYGO 콘텐츠 워크스페이스</h1><p className="mt-5">로그인 후 이용하실 수 있습니다.</p><Link href="/login" className="mt-4 inline-flex rounded bg-slate-900 px-5 py-3 text-white">로그인</Link></main>;
  const mgmt = getTenantManagementNumber(session);
  const boards = await listBoards(mgmt, { includeAdminOnly: false });
  const available = new Set(boards.map(b=>b.slug));
  return <main className="min-h-screen bg-[#f6f7fa] p-5 text-slate-900 md:p-12">
    <div className="mx-auto max-w-6xl">
      <div className="text-xs font-semibold uppercase tracking-[.23em] text-[#b8945c]">LAWYGO / CONTENT HUB</div>
      <h1 className="mt-3 font-serif text-4xl font-bold">로이고 통합 콘텐츠 관리</h1>
      <p className="mt-4 text-slate-600">기존 로이고 회원 권한·테넌트·네이티브 게시판과 연결합니다. 공개 콘텐츠와 비공개 법률 노트를 분리합니다.</p>
      <div className="mt-10 grid gap-5 md:grid-cols-2">
        {modules.map(m=>{
          const url = m.board ? `/board/${m.board}` : '/board/ai/legal_notebook';
          const hasBoard = !m.board || available.has(m.board);
          return <section key={m.slug} className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
            <span className="text-3xl text-[#b8945c]">{m.icon}</span>
            <div className="mt-3 text-xs tracking-[.15em] text-slate-500">{m.label}</div>
            <h2 className="mt-2 font-serif text-2xl font-bold">{m.name}</h2>
            <p className="my-5 text-sm text-slate-600">{m.desc}</p>
            {hasBoard ? <Link className="inline-flex rounded-lg bg-[#10263c] px-5 py-3 text-sm font-semibold text-white" href={url}>기존 엔진에서 열기 →</Link>:
              <p className="text-sm text-amber-700">게시판 DB 마이그레이션과 초기 시드 확인이 필요합니다.</p>}
          </section>;
        })}
      </div>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link className="rounded-lg border border-slate-300 bg-white px-5 py-3 text-sm font-semibold" href="/admin/settings/boards">게시판 생성·편집·삭제</Link>
        <Link className="rounded-lg border border-slate-300 bg-white px-5 py-3 text-sm font-semibold" href="/board/ai/legal_encyclopedia">기존 법률백과 AI</Link>
        <Link className="rounded-lg border border-slate-300 bg-white px-5 py-3 text-sm font-semibold" href="/board">게시판 전체</Link>
      </div>
      <p className="mt-8 text-xs text-slate-500">주의: 이 허브는 기존 서비스의 게시판·노트 화면을 연결합니다. 신규 Python CMS와의 자동 DB 동기화를 수행하지 않습니다.</p>
    </div>
  </main>;
}
