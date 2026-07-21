# Spec2Repo oracle - atomic tests for authlib-fullrepro-001
# Source: selected tests from filter/rewritten_upstream_tests.py

import base64

import copy

import datetime

import json

import os

import pytest

from cryptography.exceptions import InvalidTag

from cryptography.hazmat.primitives.keywrap import InvalidUnwrap

from authlib.jose import ECKey

from authlib.jose import JsonWebEncryption

from authlib.jose import JsonWebKey

from authlib.jose import JsonWebSignature

from authlib.jose import JsonWebToken

from authlib.jose import JWTClaims

from authlib.jose import KeySet

from authlib.jose import OctKey

from authlib.jose import OKPKey

from authlib.jose import RSAKey

from authlib.jose import errors

from authlib.jose import jwt

from authlib.jose.errors import DecodeError

from authlib.jose.errors import InvalidAlgorithmForMultipleRecipientsMode

from authlib.jose.errors import InvalidHeaderParameterNameError

from authlib.jose.errors import UnsupportedAlgorithmError

TEST_FILES = {'ed25519-pkcs8.pem': '-----BEGIN PRIVATE KEY-----\nMC4CAQAwBQYDK2VwBCIEIJ1hsZ3v/VpguoRK9JLsLMREScVpezJpGXA7rAMcrn9g\n-----END PRIVATE KEY-----\n', 'ed25519-pub.pem': '-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEA11qYAYKxCrfVS/7TyWQHOg7hcvPapiMlrwIaaPcHURo=\n-----END PUBLIC KEY-----\n', 'ed25519-ssh.pub': 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAA/RNCWJ6VfjsWW3fGjdbeM+9VbX+iXCQu02B09Bw24 demo@authlib.org\n', 'jwk_private.json': {'kty': 'RSA', 'kid': 'bilbo.baggins@hobbiton.example', 'use': 'sig', 'n': 'n4EPtAOCc9AlkeQHPzHStgAbgs7bTZLwUBZdR8_KuKPEHLd4rHVTeT-O-XV2jRojdNhxJWTDvNd7nqQ0VEiZQHz_AJmSCpMaJMRBSFKrKb2wqVwGU_NsYOYL-QtiWN2lbzcEe6XC0dApr5ydQLrHqkHHig3RBordaZ6Aj-oBHqFEHYpPe7Tpe-OfVfHd1E6cS6M1FZcD1NNLYD5lFHpPI9bTwJlsde3uhGqC0ZCuEHg8lhzwOHrtIQbS0FVbb9k3-tVTU4fg_3L_vniUFAKwuCLqKnS2BYwdq_mzSnbLY7h_qixoR7jig3__kRhuaxwUkRz5iaiQkqgc5gHdrNP5zw', 'e': 'AQAB', 'd': 'bWUC9B-EFRIo8kpGfh0ZuyGPvMNKvYWNtB_ikiH9k20eT-O1q_I78eiZkpXxXQ0UTEs2LsNRS-8uJbvQ-A1irkwMSMkK1J3XTGgdrhCku9gRldY7sNA_AKZGh-Q661_42rINLRCe8W-nZ34ui_qOfkLnK9QWDDqpaIsA-bMwWWSDFu2MUBYwkHTMEzLYGqOe04noqeq1hExBTHBOBdkMXiuFhUq1BU6l-DqEiWxqg82sXt2h-LMnT3046AOYJoRioz75tSUQfGCshWTBnP5uDjd18kKhyv07lhfSJdrPdM5Plyl21hsFf4L_mHCuoFau7gdsPfHPxxjVOcOpBrQzwQ', 'p': '3Slxg_DwTXJcb6095RoXygQCAZ5RnAvZlno1yhHtnUex_fp7AZ_9nRaO7HX_-SFfGQeutao2TDjDAWU4Vupk8rw9JR0AzZ0N2fvuIAmr_WCsmGpeNqQnev1T7IyEsnh8UMt-n5CafhkikzhEsrmndH6LxOrvRJlsPp6Zv8bUq0k', 'q': 'uKE2dh-cTf6ERF4k4e_jy78GfPYUIaUyoSSJuBzp3Cubk3OCqs6grT8bR_cu0Dm1MZwWmtdqDyI95HrUeq3MP15vMMON8lHTeZu2lmKvwqW7anV5UzhM1iZ7z4yMkuUwFWoBvyY898EXvRD-hdqRxHlSqAZ192zB3pVFJ0s7pFc', 'dp': 'B8PVvXkvJrj2L-GYQ7v3y9r6Kw5g9SahXBwsWUzp19TVlgI-YV85q1NIb1rxQtD-IsXXR3-TanevuRPRt5OBOdiMGQp8pbt26gljYfKU_E9xn-RULHz0-ed9E9gXLKD4VGngpz-PfQ_q29pk5xWHoJp009Qf1HvChixRX59ehik', 'dq': 'CLDmDGduhylc9o7r84rEUVn7pzQ6PF83Y-iBZx5NT-TpnOZKF1pErAMVeKzFEl41DlHHqqBLSM0W1sOFbwTxYWZDm6sI6og5iTbwQGIC3gnJKbi_7k_vJgGHwHxgPaX2PnvP-zyEkDERuf-ry4c_Z11Cq9AqC2yeL6kdKT1cYF8', 'qi': '3PiqvXQN0zwMeE-sBvZgi289XP9XCQF3VWqPzMKnIgQp7_Tugo6-NZBKCQsMf3HaEGBjTVJs_jcK8-TRXvaKe-7ZMaQj8VfBdYkssbu0NKDDhjJ-GtiseaDVWt7dcH0cfwxgFUHpQh7FoCrjFJ6h6ZEpMF6xmujs4qMpPz8aaI4'}, 'jwk_public.json': {'kty': 'RSA', 'kid': 'bilbo.baggins@hobbiton.example', 'use': 'sig', 'n': 'n4EPtAOCc9AlkeQHPzHStgAbgs7bTZLwUBZdR8_KuKPEHLd4rHVTeT-O-XV2jRojdNhxJWTDvNd7nqQ0VEiZQHz_AJmSCpMaJMRBSFKrKb2wqVwGU_NsYOYL-QtiWN2lbzcEe6XC0dApr5ydQLrHqkHHig3RBordaZ6Aj-oBHqFEHYpPe7Tpe-OfVfHd1E6cS6M1FZcD1NNLYD5lFHpPI9bTwJlsde3uhGqC0ZCuEHg8lhzwOHrtIQbS0FVbb9k3-tVTU4fg_3L_vniUFAKwuCLqKnS2BYwdq_mzSnbLY7h_qixoR7jig3__kRhuaxwUkRz5iaiQkqgc5gHdrNP5zw', 'e': 'AQAB'}, 'jwks_private.json': {'keys': [{'kty': 'RSA', 'kid': 'abc', 'n': 'pF1JaMSN8TEsh4N4O_5SpEAVLivJyLH-Cgl3OQBPGgJkt8cg49oasl-5iJS-VdrILxWM9_JCJyURpUuslX4Eb4eUBtQ0x5BaPa8-S2NLdGTaL7nBOO8o8n0C5FEUU-qlEip79KE8aqOj-OC44VsIquSmOvWIQD26n3fCVlgwoRBD1gzzsDOeaSyzpKrZR851Kh6rEmF2qjJ8jt6EkxMsRNACmBomzgA4M1TTsisSUO87444pe35Z4_n5c735o2fZMrGgMwiJNh7rT8SYxtIkxngioiGnwkxGQxQ4NzPAHg-XSY0J04pNm7KqTkgtxyrqOANJLIjXlR-U9SQ90NjHVQ', 'e': 'AQAB', 'd': 'G4E84ppZwm3fLMI0YZ26iJ_sq3BKcRpQD6_r0o8ZrZmO7y4Uc-ywoP7h1lhFzaox66cokuloZpKOdGHIfK-84EkI3WeveWHPqBjmTMlN_ClQVcI48mUbLhD7Zeenhi9y9ipD2fkNWi8OJny8k4GfXrGqm50w8schrsPksnxJjvocGMT6KZNfDURKF2HlM5X1uY8VCofokXOjBEeHIfYM8e7IcmPpyXwXKonDmVVbMbefo-u-TttgeyOYaO6s3flSy6Y0CnpWi43JQ_VEARxQl6Brj1oizr8UnQQ0nNCOWwDNVtOV4eSl7PZoiiT7CxYkYnhJXECMAM5YBpm4Qk9zdQ', 'p': '1g4ZGrXOuo75p9_MRIepXGpBWxip4V7B9XmO9WzPCv8nMorJntWBmsYV1I01aITxadHatO4Gl2xLniNkDyrEQzJ7w38RQgsVK-CqbnC0K9N77QPbHeC1YQd9RCNyUohOimKvb7jyv798FBU1GO5QI2eNgfnnfteSVXhD2iOoTOs', 'q': 'xJJ-8toxJdnLa0uUsAbql6zeNXGbUBMzu3FomKlyuWuq841jS2kIalaO_TRj5hbnE45jmCjeLgTVO6Ach3Wfk4zrqajqfFJ0zUg_Wexp49lC3RWiV4icBb85Q6bzeJD9Dn9vhjpfWVkczf_NeA1fGH_pcgfkT6Dm706GFFttLL8', 'dp': 'Zfx3l5NR-O8QIhzuHSSp279Afl_E6P0V2phdNa_vAaVKDrmzkHrXcl-4nPnenXrh7vIuiw_xkgnmCWWBUfylYALYlu-e0GGpZ6t2aIJIRa1QmT_CEX0zzhQcae-dk5cgHK0iO0_aUOOyAXuNPeClzAiVknz4ACZDsXdIlNFyaZs', 'dq': 'Z9DG4xOBKXBhEoWUPXMpqnlN0gPx9tRtWe2HRDkZsfu_CWn-qvEJ1L9qPSfSKs6ls5pb1xyeWseKpjblWlUwtgiS3cOsM4SI03H4o1FMi11PBtxKJNitLgvT_nrJ0z8fpux-xfFGMjXyFImoxmKpepLzg5nPZo6f6HscLNwsSJk', 'qi': 'Sk20wFvilpRKHq79xxFWiDUPHi0x0pp82dYIEntGQkKUWkbSlhgf3MAi5NEQTDmXdnB-rVeWIvEi-BXfdnNgdn8eC4zSdtF4sIAhYr5VWZo0WVWDhT7u2ccvZBFymiz8lo3gN57wGUCi9pbZqzV1-ZppX6YTNDdDCE0q-KO3Cec'}, {'kty': 'RSA', 'kid': 'bilbo.baggins@hobbiton.example', 'use': 'sig', 'n': 'n4EPtAOCc9AlkeQHPzHStgAbgs7bTZLwUBZdR8_KuKPEHLd4rHVTeT-O-XV2jRojdNhxJWTDvNd7nqQ0VEiZQHz_AJmSCpMaJMRBSFKrKb2wqVwGU_NsYOYL-QtiWN2lbzcEe6XC0dApr5ydQLrHqkHHig3RBordaZ6Aj-oBHqFEHYpPe7Tpe-OfVfHd1E6cS6M1FZcD1NNLYD5lFHpPI9bTwJlsde3uhGqC0ZCuEHg8lhzwOHrtIQbS0FVbb9k3-tVTU4fg_3L_vniUFAKwuCLqKnS2BYwdq_mzSnbLY7h_qixoR7jig3__kRhuaxwUkRz5iaiQkqgc5gHdrNP5zw', 'e': 'AQAB', 'd': 'bWUC9B-EFRIo8kpGfh0ZuyGPvMNKvYWNtB_ikiH9k20eT-O1q_I78eiZkpXxXQ0UTEs2LsNRS-8uJbvQ-A1irkwMSMkK1J3XTGgdrhCku9gRldY7sNA_AKZGh-Q661_42rINLRCe8W-nZ34ui_qOfkLnK9QWDDqpaIsA-bMwWWSDFu2MUBYwkHTMEzLYGqOe04noqeq1hExBTHBOBdkMXiuFhUq1BU6l-DqEiWxqg82sXt2h-LMnT3046AOYJoRioz75tSUQfGCshWTBnP5uDjd18kKhyv07lhfSJdrPdM5Plyl21hsFf4L_mHCuoFau7gdsPfHPxxjVOcOpBrQzwQ', 'p': '3Slxg_DwTXJcb6095RoXygQCAZ5RnAvZlno1yhHtnUex_fp7AZ_9nRaO7HX_-SFfGQeutao2TDjDAWU4Vupk8rw9JR0AzZ0N2fvuIAmr_WCsmGpeNqQnev1T7IyEsnh8UMt-n5CafhkikzhEsrmndH6LxOrvRJlsPp6Zv8bUq0k', 'q': 'uKE2dh-cTf6ERF4k4e_jy78GfPYUIaUyoSSJuBzp3Cubk3OCqs6grT8bR_cu0Dm1MZwWmtdqDyI95HrUeq3MP15vMMON8lHTeZu2lmKvwqW7anV5UzhM1iZ7z4yMkuUwFWoBvyY898EXvRD-hdqRxHlSqAZ192zB3pVFJ0s7pFc', 'dp': 'B8PVvXkvJrj2L-GYQ7v3y9r6Kw5g9SahXBwsWUzp19TVlgI-YV85q1NIb1rxQtD-IsXXR3-TanevuRPRt5OBOdiMGQp8pbt26gljYfKU_E9xn-RULHz0-ed9E9gXLKD4VGngpz-PfQ_q29pk5xWHoJp009Qf1HvChixRX59ehik', 'dq': 'CLDmDGduhylc9o7r84rEUVn7pzQ6PF83Y-iBZx5NT-TpnOZKF1pErAMVeKzFEl41DlHHqqBLSM0W1sOFbwTxYWZDm6sI6og5iTbwQGIC3gnJKbi_7k_vJgGHwHxgPaX2PnvP-zyEkDERuf-ry4c_Z11Cq9AqC2yeL6kdKT1cYF8', 'qi': '3PiqvXQN0zwMeE-sBvZgi289XP9XCQF3VWqPzMKnIgQp7_Tugo6-NZBKCQsMf3HaEGBjTVJs_jcK8-TRXvaKe-7ZMaQj8VfBdYkssbu0NKDDhjJ-GtiseaDVWt7dcH0cfwxgFUHpQh7FoCrjFJ6h6ZEpMF6xmujs4qMpPz8aaI4'}]}, 'jwks_public.json': {'keys': [{'kty': 'RSA', 'kid': 'abc', 'n': 'pF1JaMSN8TEsh4N4O_5SpEAVLivJyLH-Cgl3OQBPGgJkt8cg49oasl-5iJS-VdrILxWM9_JCJyURpUuslX4Eb4eUBtQ0x5BaPa8-S2NLdGTaL7nBOO8o8n0C5FEUU-qlEip79KE8aqOj-OC44VsIquSmOvWIQD26n3fCVlgwoRBD1gzzsDOeaSyzpKrZR851Kh6rEmF2qjJ8jt6EkxMsRNACmBomzgA4M1TTsisSUO87444pe35Z4_n5c735o2fZMrGgMwiJNh7rT8SYxtIkxngioiGnwkxGQxQ4NzPAHg-XSY0J04pNm7KqTkgtxyrqOANJLIjXlR-U9SQ90NjHVQ', 'e': 'AQAB'}, {'kty': 'RSA', 'kid': 'bilbo.baggins@hobbiton.example', 'use': 'sig', 'n': 'n4EPtAOCc9AlkeQHPzHStgAbgs7bTZLwUBZdR8_KuKPEHLd4rHVTeT-O-XV2jRojdNhxJWTDvNd7nqQ0VEiZQHz_AJmSCpMaJMRBSFKrKb2wqVwGU_NsYOYL-QtiWN2lbzcEe6XC0dApr5ydQLrHqkHHig3RBordaZ6Aj-oBHqFEHYpPe7Tpe-OfVfHd1E6cS6M1FZcD1NNLYD5lFHpPI9bTwJlsde3uhGqC0ZCuEHg8lhzwOHrtIQbS0FVbb9k3-tVTU4fg_3L_vniUFAKwuCLqKnS2BYwdq_mzSnbLY7h_qixoR7jig3__kRhuaxwUkRz5iaiQkqgc5gHdrNP5zw', 'e': 'AQAB'}]}, 'jwks_single_private.json': {'keys': [{'kty': 'RSA', 'n': 'pF1JaMSN8TEsh4N4O_5SpEAVLivJyLH-Cgl3OQBPGgJkt8cg49oasl-5iJS-VdrILxWM9_JCJyURpUuslX4Eb4eUBtQ0x5BaPa8-S2NLdGTaL7nBOO8o8n0C5FEUU-qlEip79KE8aqOj-OC44VsIquSmOvWIQD26n3fCVlgwoRBD1gzzsDOeaSyzpKrZR851Kh6rEmF2qjJ8jt6EkxMsRNACmBomzgA4M1TTsisSUO87444pe35Z4_n5c735o2fZMrGgMwiJNh7rT8SYxtIkxngioiGnwkxGQxQ4NzPAHg-XSY0J04pNm7KqTkgtxyrqOANJLIjXlR-U9SQ90NjHVQ', 'e': 'AQAB', 'd': 'G4E84ppZwm3fLMI0YZ26iJ_sq3BKcRpQD6_r0o8ZrZmO7y4Uc-ywoP7h1lhFzaox66cokuloZpKOdGHIfK-84EkI3WeveWHPqBjmTMlN_ClQVcI48mUbLhD7Zeenhi9y9ipD2fkNWi8OJny8k4GfXrGqm50w8schrsPksnxJjvocGMT6KZNfDURKF2HlM5X1uY8VCofokXOjBEeHIfYM8e7IcmPpyXwXKonDmVVbMbefo-u-TttgeyOYaO6s3flSy6Y0CnpWi43JQ_VEARxQl6Brj1oizr8UnQQ0nNCOWwDNVtOV4eSl7PZoiiT7CxYkYnhJXECMAM5YBpm4Qk9zdQ', 'p': '1g4ZGrXOuo75p9_MRIepXGpBWxip4V7B9XmO9WzPCv8nMorJntWBmsYV1I01aITxadHatO4Gl2xLniNkDyrEQzJ7w38RQgsVK-CqbnC0K9N77QPbHeC1YQd9RCNyUohOimKvb7jyv798FBU1GO5QI2eNgfnnfteSVXhD2iOoTOs', 'q': 'xJJ-8toxJdnLa0uUsAbql6zeNXGbUBMzu3FomKlyuWuq841jS2kIalaO_TRj5hbnE45jmCjeLgTVO6Ach3Wfk4zrqajqfFJ0zUg_Wexp49lC3RWiV4icBb85Q6bzeJD9Dn9vhjpfWVkczf_NeA1fGH_pcgfkT6Dm706GFFttLL8', 'dp': 'Zfx3l5NR-O8QIhzuHSSp279Afl_E6P0V2phdNa_vAaVKDrmzkHrXcl-4nPnenXrh7vIuiw_xkgnmCWWBUfylYALYlu-e0GGpZ6t2aIJIRa1QmT_CEX0zzhQcae-dk5cgHK0iO0_aUOOyAXuNPeClzAiVknz4ACZDsXdIlNFyaZs', 'dq': 'Z9DG4xOBKXBhEoWUPXMpqnlN0gPx9tRtWe2HRDkZsfu_CWn-qvEJ1L9qPSfSKs6ls5pb1xyeWseKpjblWlUwtgiS3cOsM4SI03H4o1FMi11PBtxKJNitLgvT_nrJ0z8fpux-xfFGMjXyFImoxmKpepLzg5nPZo6f6HscLNwsSJk', 'qi': 'Sk20wFvilpRKHq79xxFWiDUPHi0x0pp82dYIEntGQkKUWkbSlhgf3MAi5NEQTDmXdnB-rVeWIvEi-BXfdnNgdn8eC4zSdtF4sIAhYr5VWZo0WVWDhT7u2ccvZBFymiz8lo3gN57wGUCi9pbZqzV1-ZppX6YTNDdDCE0q-KO3Cec'}]}, 'jwks_single_public.json': {'keys': [{'kty': 'RSA', 'kid': 'abc', 'n': 'pF1JaMSN8TEsh4N4O_5SpEAVLivJyLH-Cgl3OQBPGgJkt8cg49oasl-5iJS-VdrILxWM9_JCJyURpUuslX4Eb4eUBtQ0x5BaPa8-S2NLdGTaL7nBOO8o8n0C5FEUU-qlEip79KE8aqOj-OC44VsIquSmOvWIQD26n3fCVlgwoRBD1gzzsDOeaSyzpKrZR851Kh6rEmF2qjJ8jt6EkxMsRNACmBomzgA4M1TTsisSUO87444pe35Z4_n5c735o2fZMrGgMwiJNh7rT8SYxtIkxngioiGnwkxGQxQ4NzPAHg-XSY0J04pNm7KqTkgtxyrqOANJLIjXlR-U9SQ90NjHVQ', 'e': 'AQAB'}]}, 'rsa_private.pem': '-----BEGIN RSA PRIVATE KEY-----\nMIIEogIBAAKCAQEApF1JaMSN8TEsh4N4O/5SpEAVLivJyLH+Cgl3OQBPGgJkt8cg\n49oasl+5iJS+VdrILxWM9/JCJyURpUuslX4Eb4eUBtQ0x5BaPa8+S2NLdGTaL7nB\nOO8o8n0C5FEUU+qlEip79KE8aqOj+OC44VsIquSmOvWIQD26n3fCVlgwoRBD1gzz\nsDOeaSyzpKrZR851Kh6rEmF2qjJ8jt6EkxMsRNACmBomzgA4M1TTsisSUO87444p\ne35Z4/n5c735o2fZMrGgMwiJNh7rT8SYxtIkxngioiGnwkxGQxQ4NzPAHg+XSY0J\n04pNm7KqTkgtxyrqOANJLIjXlR+U9SQ90NjHVQIDAQABAoIBABuBPOKaWcJt3yzC\nNGGduoif7KtwSnEaUA+v69KPGa2Zju8uFHPssKD+4dZYRc2qMeunKJLpaGaSjnRh\nyHyvvOBJCN1nr3lhz6gY5kzJTfwpUFXCOPJlGy4Q+2Xnp4YvcvYqQ9n5DVovDiZ8\nvJOBn16xqpudMPLHIa7D5LJ8SY76HBjE+imTXw1EShdh5TOV9bmPFQqH6JFzowRH\nhyH2DPHuyHJj6cl8FyqJw5lVWzG3n6Prvk7bYHsjmGjurN35UsumNAp6VouNyUP1\nRAEcUJega49aIs6/FJ0ENJzQjlsAzVbTleHkpez2aIok+wsWJGJ4SVxAjADOWAaZ\nuEJPc3UCgYEA1g4ZGrXOuo75p9/MRIepXGpBWxip4V7B9XmO9WzPCv8nMorJntWB\nmsYV1I01aITxadHatO4Gl2xLniNkDyrEQzJ7w38RQgsVK+CqbnC0K9N77QPbHeC1\nYQd9RCNyUohOimKvb7jyv798FBU1GO5QI2eNgfnnfteSVXhD2iOoTOsCgYEAxJJ+\n8toxJdnLa0uUsAbql6zeNXGbUBMzu3FomKlyuWuq841jS2kIalaO/TRj5hbnE45j\nmCjeLgTVO6Ach3Wfk4zrqajqfFJ0zUg/Wexp49lC3RWiV4icBb85Q6bzeJD9Dn9v\nhjpfWVkczf/NeA1fGH/pcgfkT6Dm706GFFttLL8CgYBl/HeXk1H47xAiHO4dJKnb\nv0B+X8To/RXamF01r+8BpUoOubOQetdyX7ic+d6deuHu8i6LD/GSCeYJZYFR/KVg\nAtiW757QYalnq3ZogkhFrVCZP8IRfTPOFBxp752TlyAcrSI7T9pQ47IBe4094KXM\nCJWSfPgAJkOxd0iU0XJpmwKBgGfQxuMTgSlwYRKFlD1zKap5TdID8fbUbVnth0Q5\nGbH7vwlp/qrxCdS/aj0n0irOpbOaW9ccnlrHiqY25VpVMLYIkt3DrDOEiNNx+KNR\nTItdTwbcSiTYrS4L0/56ydM/H6bsfsXxRjI18hSJqMZiqXqS84OZz2aOn+h7HCzc\nLEiZAoGASk20wFvilpRKHq79xxFWiDUPHi0x0pp82dYIEntGQkKUWkbSlhgf3MAi\n5NEQTDmXdnB+rVeWIvEi+BXfdnNgdn8eC4zSdtF4sIAhYr5VWZo0WVWDhT7u2ccv\nZBFymiz8lo3gN57wGUCi9pbZqzV1+ZppX6YTNDdDCE0q+KO3Cec=\n-----END RSA PRIVATE KEY-----\n', 'rsa_public.pem': '-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApF1JaMSN8TEsh4N4O/5S\npEAVLivJyLH+Cgl3OQBPGgJkt8cg49oasl+5iJS+VdrILxWM9/JCJyURpUuslX4E\nb4eUBtQ0x5BaPa8+S2NLdGTaL7nBOO8o8n0C5FEUU+qlEip79KE8aqOj+OC44VsI\nquSmOvWIQD26n3fCVlgwoRBD1gzzsDOeaSyzpKrZR851Kh6rEmF2qjJ8jt6EkxMs\nRNACmBomzgA4M1TTsisSUO87444pe35Z4/n5c735o2fZMrGgMwiJNh7rT8SYxtIk\nxngioiGnwkxGQxQ4NzPAHg+XSY0J04pNm7KqTkgtxyrqOANJLIjXlR+U9SQ90NjH\nVQIDAQAB\n-----END PUBLIC KEY-----\n', 'secp256k1-private.pem': '-----BEGIN PRIVATE KEY-----\nMIGEAgEAMBAGByqGSM49AgEGBSuBBAAKBG0wawIBAQQgTHXBopHraQcg1U8bPK63\neO5tNMt5ZcHo/1RsJkSnLAahRANCAAROhceIcao7c/9Ei6PgBLr3+UgDbkxSCJ0d\nKDtXgKipXfrI1mVHys/FJ0TzvNPCEZNpPPeWYd/sr5V6ADhdQsHe\n-----END PRIVATE KEY-----\n', 'secp256k1-pub.pem': '-----BEGIN PUBLIC KEY-----\nMFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAEToXHiHGqO3P/RIuj4AS69/lIA25MUgid\nHSg7V4CoqV36yNZlR8rPxSdE87zTwhGTaTz3lmHf7K+VegA4XULB3g==\n-----END PUBLIC KEY-----\n', 'secp521r1-private.json': {'kty': 'EC', 'kid': 'bilbo.baggins@hobbiton.example', 'use': 'sig', 'crv': 'P-521', 'x': 'AHKZLLOsCOzz5cY97ewNUajB957y-C-U88c3v13nmGZx6sYl_oJXu9A5RkTKqjqvjyekWF-7ytDyRXYgCF5cj0Kt', 'y': 'AdymlHvOiLxXkEhayXQnNCvDX4h9htZaCJN34kfmC6pV5OhQHiraVySsUdaQkAgDPrwQrJmbnX9cwlGfP-HqHZR1', 'd': 'AAhRON2r9cqXX1hg-RoI6R1tX5p2rUAYdmpHZoC1XNM56KtscrX6zbKipQrCW9CGZH3T4ubpnoTKLDYJ_fF3_rJt'}, 'secp521r1-public.json': {'kty': 'EC', 'kid': 'bilbo.baggins@hobbiton.example', 'use': 'sig', 'crv': 'P-521', 'x': 'AHKZLLOsCOzz5cY97ewNUajB957y-C-U88c3v13nmGZx6sYl_oJXu9A5RkTKqjqvjyekWF-7ytDyRXYgCF5cj0Kt', 'y': 'AdymlHvOiLxXkEhayXQnNCvDX4h9htZaCJN34kfmC6pV5OhQHiraVySsUdaQkAgDPrwQrJmbnX9cwlGfP-HqHZR1'}, 'ssh_private.pem': '-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABFwAAAAdzc2gtcn\nNhAAAAAwEAAQAAAQEApvV61Iw9YMrS8pAC9NAPf6ESkqNSpROGu+T0/hR7jSohlUpQk/C3\n65Zjlw+ivCY0WQeTrYMmqixx1UgSn4b6BDehsMAG72LugMO1edsXqhvhbXxEjZiogEHpkl\nA8u2O9fqaSaA2OcmQs+v7ptGAwYTxIPIM/5A4l8NKfwQy4qNrjPbFaDUQF8v6Y6/PgmoIm\nsT9eLKxcb2qZ0inBh7IdeeNoeJD25vql7qGrZrNizxf2QrmdvHLOk8a38jsVVnxf48/0pc\nH8jy+wMaeBEwlB1W68joFndKdSr+Nf8uYSCULeQRE3yTKPsNEJsODvtAWipWtA73UAc5fZ\nkTH69QXf7QAAA8jT7CeP0+wnjwAAAAdzc2gtcnNhAAABAQCm9XrUjD1gytLykAL00A9/oR\nKSo1KlE4a75PT+FHuNKiGVSlCT8LfrlmOXD6K8JjRZB5OtgyaqLHHVSBKfhvoEN6GwwAbv\nYu6Aw7V52xeqG+FtfESNmKiAQemSUDy7Y71+ppJoDY5yZCz6/um0YDBhPEg8gz/kDiXw0p\n/BDLio2uM9sVoNRAXy/pjr8+CagiaxP14srFxvapnSKcGHsh1542h4kPbm+qXuoatms2LP\nF/ZCuZ28cs6TxrfyOxVWfF/jz/SlwfyPL7Axp4ETCUHVbryOgWd0p1Kv41/y5hIJQt5BET\nfJMo+w0Qmw4O+0BaKla0DvdQBzl9mRMfr1Bd/tAAAAAwEAAQAAAQAHB1iXcBv5YjCFQ6jM\nM6IjZl2IzNVi27KVYGsr8yLMa5SkW0+PGtgzU853gpIAR792bAo8iMPs8BgOuY0HKECIQu\ntMrJjeJRUTWKngKmgRokDYQh4EtAOL+rphjX0xCl7k4RBSzxdLG4qFOowOKup+fXIxEflz\nmWDhhYxyLR3tBdCR64jm36oYuGZLv3UAH3p8CWrXW/EiWfHmiiEEtVsgVXZtX/QMKezJh0\n2BNBIGOa2bXV+I4sdrq/f49vLO0YiGaQ/Zx85fmzfoBMlQexqKWW/zbtxebf0sE9r5HAtv\nTb3LqXyb5Dqy1JI00Sm77QoZgiz524sRRwVTUyN0os9hAAAAgDEID/fmFnPcdHtX6Gnlkr\nfyivhrWUJGt1jmZLrXrCTB80XXJOF5yhym2p6Hwr3JDQKIIu6+eVUpnsMHeiU8WTBSKbnP\nBhtJFi/1uTLpJgTfLOZS7CewCkGqAIiUlVybz2GdIeyEKFwOkKwRSN7OqdanIoIX8zi7P8\nn/24xflap7AAAAgQDavsAywdgi96CdC7FIZK4X5nZuI7C7rrgPUkEb9KPnfNlT+N0QNIFK\nxyFfB0L3m2eGpJRKTtMGl1zKuD+Ecl729bnHqKKnbprd+jUlR8Bg9+Aq/rJtUue3nLBg08\n0bBUNewDmTp9R96uNr4ZiGYV6d3+ampgQ6+mukKKP6H8D6JQAAAIEAw2Tb6/c1+uKjwiYP\nHvnvpupXeFw7srnqp2eAxB3UmvhAqUB6tH0H+YADCFATbMB5nUPdnFW/q+wj0AE0R7Qcun\n7HvwztlZN9ZCYfvzy5hSZN3jdOk/I1TAObv6iDhuV0ZplP3kXZDPFT3VU7vcBBUkp04G5S\nWBgEKVBjECn1kCkAAAAQZGVtb0BhdXRobGliLm9yZwECAw==\n-----END OPENSSH PRIVATE KEY-----\n', 'ssh_public.pem': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCm9XrUjD1gytLykAL00A9/oRKSo1KlE4a75PT+FHuNKiGVSlCT8LfrlmOXD6K8JjRZB5OtgyaqLHHVSBKfhvoEN6GwwAbvYu6Aw7V52xeqG+FtfESNmKiAQemSUDy7Y71+ppJoDY5yZCz6/um0YDBhPEg8gz/kDiXw0p/BDLio2uM9sVoNRAXy/pjr8+CagiaxP14srFxvapnSKcGHsh1542h4kPbm+qXuoatms2LPF/ZCuZ28cs6TxrfyOxVWfF/jz/SlwfyPL7Axp4ETCUHVbryOgWd0p1Kv41/y5hIJQt5BETfJMo+w0Qmw4O+0BaKla0DvdQBzl9mRMfr1Bd/t demo@authlib.org\n', 'thumbprint_example.json': {'kty': 'RSA', 'n': '0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw', 'e': 'AQAB', 'alg': 'RS256', 'kid': '2011-04-29'}}

def read_file_path(name):
    value = TEST_FILES[name]
    return copy.deepcopy(value) if isinstance(value, (dict, list)) else value

def base64_to_int(value):
    raw = value.encode("ascii") if isinstance(value, str) else value
    raw += b"=" * (-len(raw) % 4)
    return int.from_bytes(base64.urlsafe_b64decode(raw), "big")

def json_dumps(value):
    return json.dumps(value)

def test_oct_import_oct_key():
    # https://tools.ietf.org/html/rfc7520#section-3.5
    obj = {
        "kty": "oct",
        "kid": "018c0ae5-4d9b-471b-bfd6-eef314bc7037",
        "use": "sig",
        "alg": "HS256",
        "k": "hJtXIZ2uSN5kbQfbtTNWbpdmhkV8FJG-Onbc6mxCcYg",
    }
    key = OctKey.import_key(obj)
    new_obj = key.as_dict()
    assert obj["k"] == new_obj["k"]
    assert "use" in new_obj

def test_oct_invalid_oct_key():
    with pytest.raises(ValueError):
        OctKey.import_key({})

def test_oct_generate_oct_key():
    with pytest.raises(ValueError):
        OctKey.generate_key(251)

    with pytest.raises(ValueError):
        OctKey.generate_key(is_private=False)

    key = OctKey.generate_key()
    assert "kid" in key.as_dict()
    assert "use" not in key.as_dict()

    key2 = OctKey.import_key(key, {"use": "sig"})
    assert "use" in key2.as_dict()

def test_rsa_import_ssh_pem():
    raw = read_file_path("ssh_public.pem")
    key = RSAKey.import_key(raw)
    obj = key.as_dict()
    assert obj["kty"] == "RSA"

def test_rsa_public_key():
    # https://tools.ietf.org/html/rfc7520#section-3.3
    obj = read_file_path("jwk_public.json")
    key = RSAKey.import_key(obj)
    new_obj = key.as_dict()
    assert base64_to_int(new_obj["n"]) == base64_to_int(obj["n"])
    assert base64_to_int(new_obj["e"]) == base64_to_int(obj["e"])

def test_rsa_private_key():
    # https://tools.ietf.org/html/rfc7520#section-3.4
    obj = read_file_path("jwk_private.json")
    key = RSAKey.import_key(obj)
    new_obj = key.as_dict(is_private=True)
    assert base64_to_int(new_obj["n"]) == base64_to_int(obj["n"])
    assert base64_to_int(new_obj["e"]) == base64_to_int(obj["e"])
    assert base64_to_int(new_obj["d"]) == base64_to_int(obj["d"])
    assert base64_to_int(new_obj["p"]) == base64_to_int(obj["p"])
    assert base64_to_int(new_obj["q"]) == base64_to_int(obj["q"])
    assert base64_to_int(new_obj["dp"]) == base64_to_int(obj["dp"])
    assert base64_to_int(new_obj["dq"]) == base64_to_int(obj["dq"])
    assert base64_to_int(new_obj["qi"]) == base64_to_int(obj["qi"])

def test_rsa_private_key2():
    rsa_obj = read_file_path("jwk_private.json")
    obj = {
        "kty": "RSA",
        "kid": "bilbo.baggins@hobbiton.example",
        "use": "sig",
        "n": rsa_obj["n"],
        "d": rsa_obj["d"],
        "e": "AQAB",
    }
    key = RSAKey.import_key(obj)
    new_obj = key.as_dict(is_private=True)
    assert base64_to_int(new_obj["n"]) == base64_to_int(obj["n"])
    assert base64_to_int(new_obj["e"]) == base64_to_int(obj["e"])
    assert base64_to_int(new_obj["d"]) == base64_to_int(obj["d"])
    assert base64_to_int(new_obj["p"]) == base64_to_int(rsa_obj["p"])
    assert base64_to_int(new_obj["q"]) == base64_to_int(rsa_obj["q"])
    assert base64_to_int(new_obj["dp"]) == base64_to_int(rsa_obj["dp"])
    assert base64_to_int(new_obj["dq"]) == base64_to_int(rsa_obj["dq"])
    assert base64_to_int(new_obj["qi"]) == base64_to_int(rsa_obj["qi"])

def test_invalid_rsa():
    with pytest.raises(ValueError):
        RSAKey.import_key({"kty": "RSA"})
    rsa_obj = read_file_path("jwk_private.json")
    obj = {
        "kty": "RSA",
        "kid": "bilbo.baggins@hobbiton.example",
        "use": "sig",
        "n": rsa_obj["n"],
        "d": rsa_obj["d"],
        "p": rsa_obj["p"],
        "e": "AQAB",
    }
    with pytest.raises(ValueError):
        RSAKey.import_key(obj)

def test_rsa_key_generate():
    with pytest.raises(ValueError):
        RSAKey.generate_key(256)
    with pytest.raises(ValueError):
        RSAKey.generate_key(2001)

    key1 = RSAKey.generate_key(is_private=True)
    private_obj = key1.as_dict(is_private=True)
    public_obj = key1.as_dict(is_private=False)
    assert private_obj["kty"] == "RSA"
    assert {"n", "e", "d", "p", "q", "dp", "dq", "qi"} <= private_obj.keys()
    assert {"n", "e"} <= public_obj.keys()

    key2 = RSAKey.generate_key(is_private=False)
    with pytest.raises(ValueError):
        key2.as_dict(True)
    assert {"n", "e"} <= key2.as_dict(is_private=False).keys()

def test_ec_public_key():
    # https://tools.ietf.org/html/rfc7520#section-3.1
    obj = read_file_path("secp521r1-public.json")
    key = ECKey.import_key(obj)
    new_obj = key.as_dict()
    assert new_obj["crv"] == obj["crv"]
    assert base64_to_int(new_obj["x"]) == base64_to_int(obj["x"])
    assert base64_to_int(new_obj["y"]) == base64_to_int(obj["y"])
    assert key.as_json()[0] == "{"

def test_not_supported_alg():
    public_key = read_file_path("rsa_public.pem")
    private_key = read_file_path("rsa_private.pem")

    jwe = JsonWebEncryption()
    s = jwe.serialize_compact(
        {"alg": "RSA-OAEP", "enc": "A256GCM"}, "hello", public_key
    )

    jwe = JsonWebEncryption(algorithms=["RSA1_5", "A256GCM"])
    with pytest.raises(errors.UnsupportedAlgorithmError):
        jwe.serialize_compact(
            {"alg": "RSA-OAEP", "enc": "A256GCM"},
            "hello",
            public_key,
        )
    with pytest.raises(errors.UnsupportedCompressionAlgorithmError):
        jwe.serialize_compact(
            {"alg": "RSA1_5", "enc": "A256GCM", "zip": "DEF"},
            "hello",
            public_key,
        )
    with pytest.raises(errors.UnsupportedAlgorithmError):
        jwe.deserialize_compact(
            s,
            private_key,
        )

    jwe = JsonWebEncryption(algorithms=["RSA-OAEP", "A192GCM"])
    with pytest.raises(errors.UnsupportedEncryptionAlgorithmError):
        jwe.serialize_compact(
            {"alg": "RSA-OAEP", "enc": "A256GCM"},
            "hello",
            public_key,
        )
    with pytest.raises(errors.UnsupportedCompressionAlgorithmError):
        jwe.serialize_compact(
            {"alg": "RSA-OAEP", "enc": "A192GCM", "zip": "DEF"},
            "hello",
            public_key,
        )
    with pytest.raises(errors.UnsupportedEncryptionAlgorithmError):
        jwe.deserialize_compact(
            s,
            private_key,
        )

def test_validate_essential_claims():
    id_token = jwt.encode({"alg": "HS256"}, {"iss": "foo"}, "k")
    claims_options = {"iss": {"essential": True, "values": ["foo"]}}
    claims = jwt.decode(id_token, "k", claims_options=claims_options)
    claims.validate()

    claims.options = {"sub": {"essential": True}}
    with pytest.raises(errors.MissingClaimError):
        claims.validate()

def test_attribute_error():
    claims = JWTClaims({"iss": "foo"}, {"alg": "HS256"})
    assert claims.iss == "foo"
    with pytest.raises(AttributeError):
        claims.invalid

def test_invalid_values():
    id_token = jwt.encode({"alg": "HS256"}, {"iss": "foo"}, "k")
    claims_options = {"iss": {"values": ["bar"]}}
    claims = jwt.decode(id_token, "k", claims_options=claims_options)
    with pytest.raises(errors.InvalidClaimError):
        claims.validate()
    claims.options = {"iss": {"value": "bar"}}
    with pytest.raises(errors.InvalidClaimError):
        claims.validate()

def test_validate_expected_issuer_received_None():
    id_token = jwt.encode({"alg": "HS256"}, {"iss": None, "sub": None}, "k")
    claims_options = {"iss": {"essential": True, "values": ["foo"]}}
    claims = jwt.decode(id_token, "k", claims_options=claims_options)
    with pytest.raises(errors.InvalidClaimError):
        claims.validate()

def test_validate_aud():
    id_token = jwt.encode({"alg": "HS256"}, {"aud": "foo"}, "k")
    claims_options = {"aud": {"essential": True, "value": "foo"}}
    claims = jwt.decode(id_token, "k", claims_options=claims_options)
    claims.validate()

    claims.options = {"aud": {"values": ["bar"]}}
    with pytest.raises(errors.InvalidClaimError):
        claims.validate()

    id_token = jwt.encode({"alg": "HS256"}, {"aud": ["foo", "bar"]}, "k")
    claims = jwt.decode(id_token, "k", claims_options=claims_options)
    claims.validate()
    # no validate
    claims.options = {"aud": {"values": []}}
    claims.validate()

def test_validate_exp():
    id_token = jwt.encode({"alg": "HS256"}, {"exp": "invalid"}, "k")
    claims = jwt.decode(id_token, "k")
    with pytest.raises(errors.InvalidClaimError):
        claims.validate()

    id_token = jwt.encode({"alg": "HS256"}, {"exp": 1234}, "k")
    claims = jwt.decode(id_token, "k")
    with pytest.raises(errors.ExpiredTokenError):
        claims.validate()

def test_validate_nbf():
    id_token = jwt.encode({"alg": "HS256"}, {"nbf": "invalid"}, "k")
    claims = jwt.decode(id_token, "k")
    with pytest.raises(errors.InvalidClaimError):
        claims.validate()

    id_token = jwt.encode({"alg": "HS256"}, {"nbf": 1234}, "k")
    claims = jwt.decode(id_token, "k")
    claims.validate()

    id_token = jwt.encode({"alg": "HS256"}, {"nbf": 1234}, "k")
    claims = jwt.decode(id_token, "k")
    with pytest.raises(errors.InvalidTokenError):
        claims.validate(123)

def test_validate_iat_issued_in_future():
    in_future = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
        seconds=10
    )
    id_token = jwt.encode({"alg": "HS256"}, {"iat": in_future}, "k")
    claims = jwt.decode(id_token, "k")
    with pytest.raises(errors.InvalidTokenError):
        claims.validate()

def test_not_enough_segments():
    s = "a.b.c"
    jwe = JsonWebEncryption()
    with pytest.raises(errors.DecodeError):
        jwe.deserialize_compact(s, None)

def test_invalid_header():
    jwe = JsonWebEncryption()
    public_key = read_file_path("rsa_public.pem")
    with pytest.raises(errors.MissingAlgorithmError):
        jwe.serialize_compact({}, "a", public_key)
    with pytest.raises(errors.UnsupportedAlgorithmError):
        jwe.serialize_compact(
            {"alg": "invalid"},
            "a",
            public_key,
        )
    with pytest.raises(errors.MissingEncryptionAlgorithmError):
        jwe.serialize_compact(
            {"alg": "RSA-OAEP"},
            "a",
            public_key,
        )
    with pytest.raises(errors.UnsupportedEncryptionAlgorithmError):
        jwe.serialize_compact(
            {"alg": "RSA-OAEP", "enc": "invalid"},
            "a",
            public_key,
        )
    with pytest.raises(errors.UnsupportedCompressionAlgorithmError):
        jwe.serialize_compact(
            {"alg": "RSA-OAEP", "enc": "A256GCM", "zip": "invalid"},
            "a",
            public_key,
        )

def test_aes_jwe_invalid_key():
    jwe = JsonWebEncryption()
    protected = {"alg": "A128KW", "enc": "A128GCM"}
    with pytest.raises(ValueError):
        jwe.serialize_compact(protected, b"hello", b"invalid-key")

def test_aes_gcm_jwe_invalid_key():
    jwe = JsonWebEncryption()
    protected = {"alg": "A128GCMKW", "enc": "A128GCM"}
    with pytest.raises(ValueError):
        jwe.serialize_compact(protected, b"hello", b"invalid-key")

def test_serialize_compact_fails_if_header_contains_unknown_field_while_private_fields_restricted():
    jwe = JsonWebEncryption(private_headers=set())
    key = OKPKey.generate_key("X25519", is_private=True)

    protected = {"alg": "ECDH-ES+A128KW", "enc": "A128GCM", "foo": "bar"}

    with pytest.raises(InvalidHeaderParameterNameError):
        jwe.serialize_compact(
            protected,
            b"hello",
            key,
        )

def test_serialize_json_fails_if_protected_header_contains_unknown_field_while_private_fields_restricted():
    jwe = JsonWebEncryption(private_headers=set())
    key = OKPKey.generate_key("X25519", is_private=True)

    protected = {"alg": "ECDH-ES+A128KW", "enc": "A128GCM", "foo": "bar"}
    header_obj = {"protected": protected}

    with pytest.raises(InvalidHeaderParameterNameError):
        jwe.serialize_json(
            header_obj,
            b"hello",
            key,
        )

def test_serialize_json_fails_if_unprotected_header_contains_unknown_field_while_private_fields_restricted():
    jwe = JsonWebEncryption(private_headers=set())
    key = OKPKey.generate_key("X25519", is_private=True)

    protected = {"alg": "ECDH-ES+A128KW", "enc": "A128GCM"}
    unprotected = {"foo": "bar"}
    header_obj = {"protected": protected, "unprotected": unprotected}

    with pytest.raises(InvalidHeaderParameterNameError):
        jwe.serialize_json(
            header_obj,
            b"hello",
            key,
        )

def test_serialize_json_fails_if_recipient_header_contains_unknown_field_while_private_fields_restricted():
    jwe = JsonWebEncryption(private_headers=set())
    key = OKPKey.generate_key("X25519", is_private=True)

    protected = {"alg": "ECDH-ES+A128KW", "enc": "A128GCM"}
    recipients = [{"header": {"foo": "bar"}}]
    header_obj = {"protected": protected, "recipients": recipients}

    with pytest.raises(InvalidHeaderParameterNameError):
        jwe.serialize_json(
            header_obj,
            b"hello",
            key,
        )

def test_deserialize_json_fails_if_unprotected_header_contains_unknown_field_while_private_fields_restricted():
    jwe = JsonWebEncryption(private_headers=set())
    key = OKPKey.generate_key("X25519", is_private=True)

    protected = {"alg": "ECDH-ES+A128KW", "enc": "A128GCM"}
    header_obj = {"protected": protected}

    data = jwe.serialize_json(header_obj, b"hello", key)

    data["unprotected"] = {"foo": "bar"}

    with pytest.raises(InvalidHeaderParameterNameError):
        jwe.deserialize_json(data, key)

def test_deserialize_json_fails_if_recipient_header_contains_unknown_field_while_private_fields_restricted():
    jwe = JsonWebEncryption(private_headers=set())
    key = OKPKey.generate_key("X25519", is_private=True)

    protected = {"alg": "ECDH-ES+A128KW", "enc": "A128GCM"}
    header_obj = {"protected": protected}

    data = jwe.serialize_json(header_obj, b"hello", key)

    data["recipients"][0]["header"] = {"foo": "bar"}

    with pytest.raises(InvalidHeaderParameterNameError):
        jwe.deserialize_json(data, key)


# Spec2Repo oracle - atomic tests for authlib-fullrepro-001
# Source: selected tests from filter/generated_tests.py

import json

import os

import subprocess

import sys

import warnings

import pytest

from authlib.jose import BaseClaims

from authlib.jose import JWSHeader

from authlib.jose import JWTClaims

from authlib.jose import JsonWebEncryption

from authlib.jose import JsonWebKey

from authlib.jose import JsonWebSignature

from authlib.jose import JsonWebToken

from authlib.jose import KeySet

from authlib.jose import OctKey

from authlib.jose import errors

from authlib.jose import jwt

from authlib.jose.errors import JoseError

def test_scope_header_validation_is_part_of_jose_behavior():
    jws = JsonWebSignature(private_headers=[])
    with pytest.raises(errors.InvalidHeaderParameterNameError):
        jws.serialize({"alg": "HS256", "not_registered": True}, b"payload", "secret")

def test_scope_claim_validation_is_part_of_jose_behavior():
    claims = JWTClaims({"iss": "issuer", "aud": ["api"]}, {}, options={"aud": {"values": ["api"]}})
    claims.validate(now=1)
    assert claims.iss == "issuer"
    assert claims.aud == ["api"]

def test_installable_surface_public_error_classes_share_jose_base():
    assert issubclass(errors.DecodeError, JoseError)
    assert errors.DecodeError.error == "decode_error"
    with pytest.raises(errors.DecodeError):
        JsonWebToken(["HS256"]).decode(b"one.two", "secret")

def test_installable_surface_importing_jose_emits_deprecation_warning():
    code = "import warnings; warnings.simplefilter('always'); import authlib.jose"
    proc = subprocess.run(
        [sys.executable, "-W", "always", "-c", code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy(),
        check=False,
    )
    assert proc.returncode == 0
    assert "AuthlibDeprecationWarning" in proc.stderr

def test_public_api_jws_header_protected_values_take_precedence():
    header = JWSHeader({"alg": "HS256", "kid": "protected"}, {"kid": "unprotected"})
    assert header["kid"] == "protected"
    assert header.protected["kid"] == "protected"
    assert header.header["kid"] == "unprotected"

def test_product_state_key_projection_round_trips_public_fields():
    private_key = OctKey.import_key("secret", {"kid": "state-key", "use": "sig"})
    exported = private_key.as_dict(is_private=True)
    imported = JsonWebKey.import_key(exported)
    assert imported.as_dict()["kid"] == "state-key"
    assert imported.as_dict()["use"] == "sig"

def test_invocation_jose_import_reports_deprecation_warning():
    code = "import warnings; warnings.simplefilter('always'); import authlib.jose"
    proc = subprocess.run(
        [sys.executable, "-W", "always", "-c", code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy(),
        check=False,
    )
    assert proc.returncode == 0
    assert "AuthlibDeprecationWarning" in proc.stderr

def test_environment_subprocess_can_validate_claims_without_services():
    code = (
        "from authlib.jose import JWTClaims; "
        "claims=JWTClaims({'sub':'env'}, {}, options={'sub': {'value': 'env'}}); "
        "claims.validate(now=1); "
        "assert claims['sub'] == 'env'"
    )
    proc = subprocess.run([sys.executable, "-W", "ignore", "-c", code], text=True, env=os.environ.copy())
    assert proc.returncode == 0

def test_evaluation_notes_public_exception_type_without_message_assertion():
    with pytest.raises(errors.DecodeError):
        JsonWebToken(["HS256"]).decode(b"one.two", "secret")

def test_evaluation_notes_json_inputs_use_public_mappings_only():
    parsed = JsonWebEncryption.parse_json(json.dumps({"protected": "abc", "recipients": []}))
    assert parsed == {"protected": "abc", "recipients": []}

def test_invocation_import_authlib_exposes_package_metadata():
    code = (
        "import authlib; "
        "assert isinstance(authlib.__version__, str) and authlib.__version__; "
        "assert authlib.__license__ == 'BSD-3-Clause'; "
        "assert authlib.__homepage__ == 'https://authlib.org'"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy(),
        check=False,
    )
    assert proc.returncode == 0
