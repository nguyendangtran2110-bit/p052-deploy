import type { DemoAccount } from "@/src/mock/data";
import type { DraftValue } from "@/src/lib/ticket-contract";

let proposal: { accountId: string; value: DraftValue } | null = null;
export function holdProposal(account: DemoAccount, value: DraftValue) { proposal = { accountId: account.id, value: { ...value } }; }
export function takeProposal(account: DemoAccount) {
  if (!proposal || proposal.accountId !== account.id) { proposal = null; return null; }
  const value = proposal.value;
  proposal = null;
  return value;
}
export function purgeClientBuffers() { proposal = null; }
