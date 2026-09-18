export function restorePersistentSession(){
 const auth=window.ristAuth;
 return auth?.sessionInfo?.()??null;
}

export function applyProviderSessionPolicy(){
 const auth=window.ristAuth;
 auth?.installSessionExpiry?.();
 return auth?.sessionInfo?.()??null;
}

// Legacy export retained only as an alias for older imports.
// Provider-issued expiry is the authority; this no longer imposes eight hours.
export const applyEightHourSessionPolicy=applyProviderSessionPolicy;
