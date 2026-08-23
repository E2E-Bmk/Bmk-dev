# Spec-to-test map

oracle_source: generated_only
oracle_version: 2026-08-21T23:15:00+08:00

| test_nodeid | layer | assertion_kind | spec_section | status | notes |
|---|---|---|---|---|---|
| atomic::TestVAL001NewIndependentValidators | atomic | positive | Error Metadata and Naming | covered | generated; VAL-ERR-001, VAL-REG-010 |
| atomic::TestVAL002Required | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-003, VAL-ERR-006 |
| atomic::TestVAL003OmitEmptySkipsRemainder | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-004 |
| atomic::TestVAL004OmitNilDistinguishesZeroPointer | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-005 |
| atomic::TestVAL005LenUsesRuneCount | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-006 |
| atomic::TestVAL006CollectionLengthRules | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-006 |
| atomic::TestVAL007NumericOrdering | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-006 |
| atomic::TestVAL008EqualityAndInequality | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-006 |
| atomic::TestVAL009OneOf | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-008 |
| atomic::TestVAL010OneOfCaseInsensitive | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-008, VAL-VALUE-009 |
| atomic::TestVAL011ContainsAndExcludes | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-008 |
| atomic::TestVAL012ContainsAny | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-008 |
| atomic::TestVAL013StartsAndEndsWith | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-008 |
| atomic::TestVAL014LowerAndUppercase | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-008 |
| atomic::TestVAL015AlphaAndAlphanum | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-008 |
| atomic::TestVAL016NumericString | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-008 |
| atomic::TestVAL017BooleanString | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-008 |
| atomic::TestVAL018Email | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-010 |
| atomic::TestVAL019URL | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-010 |
| atomic::TestVAL020IPFamilies | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-010 |
| atomic::TestVAL021CIDR | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-010 |
| atomic::TestVAL022UUID | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-010 |
| atomic::TestVAL023JSON | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-010 |
| atomic::TestVAL024Base64 | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-010 |
| atomic::TestVAL025DatetimeLayout | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-010, VAL-VALUE-011 |
| atomic::TestVAL026Timezone | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-010 |
| atomic::TestVAL027AlternativeExpression | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-012, VAL-VALUE-013 |
| atomic::TestVAL028AliasMetadata | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-014, VAL-CVI-006 |
| atomic::TestVAL029CustomValidationFieldLevel | atomic | positive | Registration and Callback Semantics | covered | generated; VAL-REG-001, VAL-REG-002 |
| atomic::TestVAL030InvalidRegistrationName | atomic | failure_path | Registration and Callback Semantics | covered | generated; VAL-REG-001, VAL-REG-011 |
| atomic::TestVAL031ContextValidationReceivesContext | atomic | positive | Registration and Callback Semantics | covered | generated; VAL-REG-003 |
| atomic::TestVAL032CustomTypeProjection | atomic | positive | Registration and Callback Semantics | covered | generated; VAL-REG-004 |
| atomic::TestVAL033ValidationErrorsCollection | atomic | positive | Error Metadata and Naming | covered | generated; VAL-ERR-002, VAL-ERR-003 |
| atomic::TestVAL034InvalidValidationError | atomic | failure_path | Error Metadata and Naming | covered | generated; VAL-ERR-004 |
| atomic::TestVAL035UndefinedTagPanics | atomic | failure_path | Error Metadata and Naming | covered | generated; VAL-ERR-005 |
| atomic::TestVAL036MalformedParameterPanics | atomic | failure_path | Error Metadata and Naming | covered | generated; VAL-ERR-005, VAL-VALUE-007 |
| atomic::TestVAL037FieldErrorValueKindType | atomic | positive | Error Metadata and Naming | covered | generated; VAL-ERR-006, VAL-CVI-001 |
| atomic::TestVAL038DiveSlice | atomic | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-010, VAL-ERR-010 |
| atomic::TestVAL039UniqueSlice | atomic | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-010, VAL-VALUE-008 |
| atomic::TestVAL040DurationOrdering | atomic | positive | Value Rules and Tag Expressions | covered | generated; VAL-VALUE-006 |
| integration::TestVAL041NestedStructTraversal | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-001, VAL-ERR-008 |
| integration::TestVAL042DashSkipsField | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-002 |
| integration::TestVAL043RequiredStructOption | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-003 |
| integration::TestVAL044StructPartialSelectsOnlyNamedFields | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-004, VAL-CVI-003 |
| integration::TestVAL045StructPartialNestedPath | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-004, VAL-ERR-008 |
| integration::TestVAL046StructExceptSkipsNamedFields | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-005, VAL-CVI-003 |
| integration::TestVAL047StructFilteredUsesNamespace | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-006, VAL-CVI-003 |
| integration::TestVAL048EqualField | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-007 |
| integration::TestVAL049GreaterThanField | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-007 |
| integration::TestVAL050RequiredIf | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-008 |
| integration::TestVAL051RequiredWithout | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-008 |
| integration::TestVAL052ExcludedIf | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-009 |
| integration::TestVAL053DiveNestedStructs | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-010, VAL-STRUCT-012, VAL-CVI-005 |
| integration::TestVAL054MapKeyAndValueDive | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-011, VAL-STRUCT-012 |
| integration::TestVAL055ValidateMapProjectsOnlyFailures | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-013, VAL-STRUCT-014 |
| integration::TestVAL056ValidateMapNestedRules | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-013, VAL-STRUCT-014 |
| integration::TestVAL057AlternateFieldNamesAndNamespaces | integration | positive | Error Metadata and Naming | covered | generated; VAL-ERR-007, VAL-ERR-009, VAL-ERR-012, VAL-CVI-002 |
| integration::TestVAL058SetTagNameSelectsRuleTag | integration | positive | Error Metadata and Naming | covered | generated; VAL-ERR-011 |
| integration::TestVAL059StructLevelReportedErrors | integration | positive | Registration and Callback Semantics | covered | generated; VAL-REG-006, VAL-REG-007, VAL-REG-008, VAL-CVI-004 |
| integration::TestVAL060StructLevelContext | integration | positive | Registration and Callback Semantics | covered | generated; VAL-REG-003, VAL-REG-006, VAL-REG-008 |
| integration::TestVAL061StructMapRulesOverrideTags | integration | positive | Registration and Callback Semantics | covered | generated; VAL-REG-009 |
| integration::TestVAL062RegistrationsAreInstanceLocal | integration | positive | Registration and Callback Semantics | covered | generated; VAL-REG-010, VAL-CVI-008 |
| integration::TestVAL063BuiltInAndCustomErrorsCompose | integration | positive | Cross-View Invariants | covered | generated; VAL-CVI-004, VAL-ERR-003 |
| integration::TestVAL064VarWithValueContextParity | integration | positive | Structures, Fields, and Collections | covered | generated; VAL-STRUCT-007, VAL-CVI-007 |
| integration::TestVAL065ContextAndPlainMapValidationAgree | integration | positive | Cross-View Invariants | covered | generated; VAL-CVI-007, VAL-STRUCT-014 |

Total: 65 | kept (covered): 65 | spec_gap: 0 | source-only: 0 | excluded: 0 | final scoreable: 65
