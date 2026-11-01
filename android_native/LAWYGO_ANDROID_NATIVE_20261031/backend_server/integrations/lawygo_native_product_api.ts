/** Drop into src/app/api/workspace/products/route.ts
 * Read-only product status in existing LAWYGO session. Never expose service-role credentials.
 */
import { NextResponse } from 'next/server';
import { requireAuthenticatedSession } from '@/lib/adminSession';
import { getTenantManagementNumber } from '@/lib/boardApiContext';
import { listBoards } from '@/lib/boardService';

export async function GET() {
  const auth = await requireAuthenticatedSession();
  if ('error' in auth) return auth.error;
  const managementNumber = getTenantManagementNumber(auth.session);
  const boards = await listBoards(managementNumber, {includeAdminOnly:false});
  const exists = new Set(boards.map(b=>b.slug));
  const items = [
    {id:'channel',board:'lawygo_channel',href:'/board/lawygo_channel'},
    {id:'wiki',board:'lawygo_wiki',href:'/board/lawygo_wiki'},
    {id:'pan',board:'lawygo_pan',href:'/board/lawygo_pan'},
    {id:'note',board:null,href:'/board/ai/legal_notebook'},
  ].map(x=>({...x,ready:x.board===null||exists.has(x.board)}));
  return NextResponse.json({success:true,items},{headers:{'Cache-Control':'private, no-store'}});
}
