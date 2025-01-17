/**
 * Copyright 2023 University of Adelaide
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { CURVE_T, METHOD_T } from "./fiat-bridge";

export const BRIDGES = ["fiat", "jasmin", "bitcoin-core", "manual"] as const;
export type BRIDGES_T = (typeof BRIDGES)[number];

// currently used only in src/CountCycle
export const KNOWN_SYMBOLS: {
  [symbol: string]: { bridge: "fiat" | "bitcoin-core"; method: METHOD_T; curve: CURVE_T };
} = {
  // fiat generated bls curves
  fiat_bls12_381_p_mul: { bridge: "fiat", method: "mul", curve: "bls12_381_p" },
  fiat_bls12_381_p_square: { bridge: "fiat", method: "square", curve: "bls12_381_p" },
  fiat_bls12_381_q_mul: { bridge: "fiat", method: "mul", curve: "bls12_381_q" },
  fiat_bls12_381_q_square: { bridge: "fiat", method: "square", curve: "bls12_381_q" },

  // fiat default curves
  fiat_curve25519_carry_mul: { bridge: "fiat", method: "mul", curve: "curve25519" },
  fiat_curve25519_carry_square: { bridge: "fiat", method: "square", curve: "curve25519" },
  fiat_curve25519_solinas_mul: { bridge: "fiat", method: "mul", curve: "curve25519_solinas" },
  /* currently not supported
   * fiat_curve25519_solinas_mul2: { bridge: "fiat", method: "mul2", curve: "curve25519_solinas" },
   */
  fiat_curve25519_solinas_square: { bridge: "fiat", method: "square", curve: "curve25519_solinas" },
  fiat_p224_mul: { bridge: "fiat", method: "mul", curve: "p224" },
  fiat_p224_square: { bridge: "fiat", method: "square", curve: "p224" },
  fiat_p256_mul: { bridge: "fiat", method: "mul", curve: "p256" },
  fiat_p256_square: { bridge: "fiat", method: "square", curve: "p256" },
  fiat_p384_mul: { bridge: "fiat", method: "mul", curve: "p384" },
  fiat_p384_square: { bridge: "fiat", method: "square", curve: "p384" },
  fiat_p434_mul: { bridge: "fiat", method: "mul", curve: "p434" },
  fiat_p434_square: { bridge: "fiat", method: "square", curve: "p434" },
  fiat_p448_solinas_carry_mul: { bridge: "fiat", method: "mul", curve: "p448_solinas" },
  fiat_p448_solinas_carry_square: { bridge: "fiat", method: "square", curve: "p448_solinas" },
  fiat_p521_carry_mul: { bridge: "fiat", method: "mul", curve: "p521" },
  fiat_p521_carry_square: { bridge: "fiat", method: "square", curve: "p521" },
  fiat_poly1305_carry_mul: { bridge: "fiat", method: "mul", curve: "poly1305" },
  fiat_poly1305_carry_square: { bridge: "fiat", method: "square", curve: "poly1305" },
  fiat_secp256k1_montgomery_mul: { bridge: "fiat", method: "mul", curve: "secp256k1_montgomery" },
  fiat_secp256k1_montgomery_square: { bridge: "fiat", method: "square", curve: "secp256k1_montgomery" },
  fiat_secp256k1_dettman_mul: { bridge: "fiat", method: "mul", curve: "secp256k1_dettman" },
  fiat_secp256k1_dettman_square: { bridge: "fiat", method: "square", curve: "secp256k1_dettman" },

  // bitcoin curve
  secp256k1_fe_mul_inner: { bridge: "bitcoin-core", method: "mul", curve: "secp256k1_dettman" },
  secp256k1_fe_sqr_inner: { bridge: "bitcoin-core", method: "square", curve: "secp256k1_dettman" },
};
