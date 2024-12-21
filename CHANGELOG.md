# Changelog

<!--next-version-placeholder-->

## v0.1.28 (2024-12-21)

### Fix

* Fix file permission defined in dashboard container ([`1ac663b`](https://github.com/gbourniq/portfolio-analytics-platform/commit/1ac663b47e6c0e3ccc26294ce7b71cdc5a63c5c3))

## v0.1.27 (2024-12-21)

### Feature

* Improve deployment experience by adding a data-specific container and shared volume ([`0e44bec`](https://github.com/gbourniq/portfolio-analytics-platform/commit/0e44bec93215791765b54a1f914781ac17c3bdd6))

### Fix

* Decrease default data coverage values for fx and equity pipeline ([`f827115`](https://github.com/gbourniq/portfolio-analytics-platform/commit/f827115aab17742773681fbda6afcb9f8f18b6ee))
* Add the data directory inside the container ([`5bcf02f`](https://github.com/gbourniq/portfolio-analytics-platform/commit/5bcf02ffb4a9b9e4155a0b97323edcdacb94caf5))

## v0.1.26 (2024-12-20)

### Fix

* Fix various issues ([`dd1f3f8`](https://github.com/gbourniq/portfolio-analytics-platform/commit/dd1f3f89d561af97649c5441c9a3d60bbd19d42b))

## v0.1.25 (2024-12-20)

### Feature

* Use Github Container Repository to publish docker images in CI ([`3eb6b4d`](https://github.com/gbourniq/portfolio-analytics-platform/commit/3eb6b4d07fd6da5275ccaff1a640905b56b0cdc4))

### Fix

* Fix semantic release ([`5bdfdef`](https://github.com/gbourniq/portfolio-analytics-platform/commit/5bdfdef7409afa222f588af1efe1ec4604d9cfb4))
* Fix semantic release ([`92a6bf8`](https://github.com/gbourniq/portfolio-analytics-platform/commit/92a6bf8f6dd0a77d87f8975fd1b04c901c7bffc6))
* Fix flakey dashboard integration test ([`d71e88e`](https://github.com/gbourniq/portfolio-analytics-platform/commit/d71e88e95a2aaa494d67217c5bab81b6bd5e04e7))

## v0.1.24 (2024-12-20)

### Fix

* Fix poetry install in dockerfiles ([`6ee3ade`](https://github.com/gbourniq/portfolio-analytics/commit/6ee3ade258da46ccd75f45287dc296f04793e1fc))

## v0.1.23 (2024-12-19)

### Feature

* Upgrade to python3.12 and remove requirements.txt files in favour of poetry ([`07e210b`](https://github.com/gbourniq/portfolio-analytics/commit/07e210b64ab5e1a19e4cc6d6f13d7a4aef02ca9a))

### Fix

* Add resource limits to containers ([`db74fc9`](https://github.com/gbourniq/portfolio-analytics/commit/db74fc931a156b272502a575832baf39847942b0))

## v0.1.22 (2024-12-19)

### Fix

* Autoscale graph axis for better view on pnl values ([#23](https://github.com/gbourniq/portfolio-analytics/issues/23)) ([`98f421a`](https://github.com/gbourniq/portfolio-analytics/commit/98f421aa152cd25170ad3be890b64a0d0c1ea12c))

## v0.1.21 (2024-12-19)

### Feature

* Implement better cache mechanism and various code improvements ([#22](https://github.com/gbourniq/portfolio-analytics/issues/22)) ([`7fc67d8`](https://github.com/gbourniq/portfolio-analytics/commit/7fc67d8d0f297d068b0ea290d39a0178016c25ff))

## v0.1.20 (2024-12-19)

### Fix

* Convert to target currency after computing pnl ([#21](https://github.com/gbourniq/portfolio-analytics/issues/21)) ([`ec091ff`](https://github.com/gbourniq/portfolio-analytics/commit/ec091ff3e5d1b7772099753b25c59514e6d102d6))

## v0.1.19 (2024-12-19)

### Fix

* Fix currency conversion ([#20](https://github.com/gbourniq/portfolio-analytics/issues/20)) ([`9fa3901`](https://github.com/gbourniq/portfolio-analytics/commit/9fa390148785eeed3933abdc7cb892fff921aeed))

## v0.1.18 (2024-12-19)



## v0.1.17 (2024-12-18)

### Fix

* Fix pnl computations when analysis is filtered by date ([#18](https://github.com/gbourniq/portfolio-analytics/issues/18)) ([`ac1c0e0`](https://github.com/gbourniq/portfolio-analytics/commit/ac1c0e01c95f565b92166673fd3f1341e245669f))

## v0.1.16 (2024-12-18)

### Feature

* Improve data coverage validation before calculating pnl ([#17](https://github.com/gbourniq/portfolio-analytics/issues/17)) ([`702b128`](https://github.com/gbourniq/portfolio-analytics/commit/702b12870945d5e0e57e780f39725faf5f4cf242))

## v0.1.15 (2024-12-18)

### Fix

* Error message showing wrong fx data coverage ([#16](https://github.com/gbourniq/portfolio-analytics/issues/16)) ([`fba9c8b`](https://github.com/gbourniq/portfolio-analytics/commit/fba9c8bacd7d8be74031df46e517875ce381f4ca))

## v0.1.14 (2024-12-18)

### Documentation

* Update readme ([#14](https://github.com/gbourniq/portfolio-analytics/issues/14)) ([`89c8410`](https://github.com/gbourniq/portfolio-analytics/commit/89c8410279b065855f52c3aa735479c8d80110a5))

## v0.1.13 (2024-12-18)

### Fix

* Quick fix for the date filtered png graph ([#13](https://github.com/gbourniq/portfolio-analytics/issues/13)) ([`37381e6`](https://github.com/gbourniq/portfolio-analytics/commit/37381e687b2262bdc118b3555b6a260751e9a8cd))

## v0.1.12 (2024-12-18)

### Fix

* Fix daily pnl calculation ([#12](https://github.com/gbourniq/portfolio-analytics/issues/12)) ([`a820b69`](https://github.com/gbourniq/portfolio-analytics/commit/a820b6984171d465aeb9f148076c85ea311ab5d5))

## v0.1.11 (2024-12-18)



## v0.1.10 (2024-12-18)

### Documentation

* Update readme ([`7919ba1`](https://github.com/gbourniq/portfolio-analytics/commit/7919ba17bda78d5acbe843d9414b065301d0c72b))

## v0.1.9 (2024-12-18)



## v0.1.8 (2024-12-18)

### Documentation

* Add more info to the market_data/equity/ endpoint description ([`72f3914`](https://github.com/gbourniq/portfolio-analytics/commit/72f391446c2872717b27d6715468df94930f81ba))

## v0.1.7 (2024-12-17)

### Fix

* Fix pylint badge ([`6e2f996`](https://github.com/gbourniq/portfolio-analytics/commit/6e2f996d113a4788058738fc3e19f35942254ea6))

## v0.1.6 (2024-12-17)

### Feature

* Calculate a more realistic pnl ([#8](https://github.com/gbourniq/portfolio-analytics/issues/8)) ([`3c98aa3`](https://github.com/gbourniq/portfolio-analytics/commit/3c98aa3154ec2c168e4d2c003225ea07b9b893ba))

## v0.1.5 (2024-12-17)



## v0.1.4 (2024-12-17)



## v0.1.3 (2024-12-17)



## v0.1.2 (2024-12-17)

### Fix

* Increase api timeout to 120s ([`310478b`](https://github.com/gbourniq/portfolio-analytics/commit/310478b6d56e10266765b61b559ff6ee7d64ba00))

## v0.1.1 (2024-12-17)

### Feature

* Test release version bump via CI ([`f8b0856`](https://github.com/gbourniq/portfolio-analytics/commit/f8b0856ae00a8790807efbe3afb77e520e7e7355))

### Fix

* Resolve semantic release locally ([`0edea7c`](https://github.com/gbourniq/portfolio-analytics/commit/0edea7cf737e35923a0c31ccd7e683a3f3e6042d))

## v0.1.0 (2024-12-17)

### Feature

* First commit ([`78b0878`](https://github.com/gbourniq/portfolio-analytics/commit/78b0878db5a516bae24c7965f3b6174624d21e93))

### Fix

* Fix semantic release ([`5f7a401`](https://github.com/gbourniq/portfolio-analytics/commit/5f7a40134c03e4c82aeb69dfc7b8604c0dedbaa6))
* Remove deprecated version key in docker-compose ([`2acf7b0`](https://github.com/gbourniq/portfolio-analytics/commit/2acf7b025d0de33be7e3c4852d3903c2328a75f8))
