// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

library Pairing {
    struct G1Point {
        uint256 X;
        uint256 Y;
    }

    struct G2Point {
        uint256 X1;
        uint256 X2;
        uint256 Y1;
        uint256 Y2;
    }


    function negate(G1Point memory p) internal pure returns (G1Point memory) {
        // p.Y should not be 0 mod p
        if (p.X == 0 && p.Y == 0) {
            return G1Point(0, 0);
        }
        // field prime for alt_bn128
        uint256 p_mod = 21888242871839275222246405745257275088548364400416034343698204186575808495617;
        return G1Point(p.X, p_mod - (p.Y % p_mod));
    }


    function pairing(G1Point[] memory p1, G2Point[] memory p2) internal view returns (bool) {
        require(p1.length == p2.length, "Pairing length mismatch");
        uint256 elements = p1.length;
        uint256 inputSize = elements * 6; // Each pair needs 6 uint256
        uint256[] memory input = new uint256[](inputSize);

        for (uint256 i = 0; i < elements; i++) {
            uint256 j = i * 6;
            input[j + 0] = p1[i].X;
            input[j + 1] = p1[i].Y;
            input[j + 2] = p2[i].X1;
            input[j + 3] = p2[i].X2;
            input[j + 4] = p2[i].Y1;
            input[j + 5] = p2[i].Y2;
        }

        // Call the precompile at 0x08 with the encoded input
        bool success;
        uint256[1] memory out;
        assembly {
            success := staticcall(
                gas(),
                0x08,
                add(input, 0x20),
                mul(inputSize, 0x20),
                out,
                0x20
            )
        }
        require(success, "pairing call failed");

        return out[0] != 0;
    }
    
    function pairingProd2(
        G1Point memory a1,
        G2Point memory a2,
        G1Point memory b1,
        G2Point memory b2
    ) internal view returns (bool) {
        G1Point[] memory p1 = new G1Point[](2);
        G2Point[] memory p2 = new G2Point[](2);
        p1[0] = a1;
        p1[1] = b1;
        p2[0] = a2;
        p2[1] = b2;
        return pairing(p1, p2);
    }
}

contract ZKVerifier {
    using Pairing for *;


    struct VerifyingKey {
        Pairing.G1Point alpha1;
        Pairing.G2Point beta2;
        Pairing.G2Point gamma2;
        Pairing.G2Point delta2;
        Pairing.G1Point[] IC; // IC = “instantiation constants” for public inputs
    }


    struct Proof {
        Pairing.G1Point A;
        Pairing.G2Point B;
        Pairing.G1Point C;
    }

    VerifyingKey vk;


    constructor() {
        vk.alpha1 = Pairing.G1Point(
            0x01,
            0x02
        );
        vk.beta2 = Pairing.G2Point(
            0x03,
            0x04,
            0x05,
            0x06
        );
        vk.gamma2 = Pairing.G2Point(
            0x07,
            0x08,
            0x09,
            0x10
        );
        vk.delta2 = Pairing.G2Point(
            0x11,
            0x12,
            0x13,
            0x14
        );
        
        vk.IC.push(Pairing.G1Point(0x111, 0x222));
        vk.IC.push(Pairing.G1Point(0x333, 0x444));
    }


    function verifyProof(
        Proof memory proof,
        uint256[2] memory input  // assume the circuit has exactly 2 public inputs
    ) public view returns (bool) {
        //   VK.IC[0] + input[0]*VK.IC[1] + input[1]*VK.IC[2] + ...
        Pairing.G1Point memory vk_x = Pairing.G1Point(vk.IC[0].X, vk.IC[0].Y);
        
        vk_x = addPoints(vk_x, scalarMul(vk.IC[1], input[0]));
        if (
            !Pairing.pairingProd2(
                proof.A,
                proof.B,
                Pairing.negate(addPoints(vk.alpha1, vk_x)),
                vk.beta2
            )
        ) {
            return false;
        }

        // e(proof.C, vk.delta2) ?= e(vk.alpha1, vk.gamma2)
        if (
            !Pairing.pairingProd2(
                proof.C,
                vk.delta2,
                Pairing.negate(vk.alpha1),
                vk.gamma2
            )
        ) {
            return false;
        }

        return true;
    }



    function addPoints(
        Pairing.G1Point memory p1,
        Pairing.G1Point memory p2
    ) internal pure returns (Pairing.G1Point memory r) {
        r.X = p1.X + p2.X; // not correct mod p in real usage
        r.Y = p1.Y + p2.Y; 
    }


    function scalarMul(
        Pairing.G1Point memory p,
        uint256 s
    ) internal pure returns (Pairing.G1Point memory r) {
        r.X = p.X * s; // not correct mod p in real usage
        r.Y = p.Y * s; 
    }
}
