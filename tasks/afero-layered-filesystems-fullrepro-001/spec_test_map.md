# Spec-to-test map

| Clause | Test node | Tier | Behavior |
|---|---|---|---|
| AFERO-001 | `atomic::TestAFERO001` | atomic | constructor and name |
| AFERO-002 | `atomic::TestAFERO002` | atomic | root directory |
| AFERO-003 | `atomic::TestAFERO003` | atomic | mkdir creates parent |
| AFERO-004 | `atomic::TestAFERO004` | atomic | mkdirall mode |
| AFERO-005 | `atomic::TestAFERO005` | atomic | create read |
| AFERO-006 | `atomic::TestAFERO006` | atomic | create truncates |
| AFERO-007 | `atomic::TestAFERO007` | atomic | exclusive create |
| AFERO-009 | `atomic::TestAFERO009` | atomic | seek gap zero filled |
| AFERO-010 | `atomic::TestAFERO010` | atomic | readat keeps offset |
| AFERO-011 | `atomic::TestAFERO011` | atomic | writeat keeps offset |
| AFERO-012 | `atomic::TestAFERO012` | atomic | truncate extends |
| AFERO-013 | `atomic::TestAFERO013` | atomic | chmod |
| AFERO-014 | `atomic::TestAFERO014` | atomic | chtimes |
| AFERO-015 | `atomic::TestAFERO015` | atomic | remove file |
| AFERO-016 | `atomic::TestAFERO016` | atomic | remove directory entry |
| AFERO-017 | `atomic::TestAFERO017` | atomic | removeall is scoped |
| AFERO-018 | `atomic::TestAFERO018` | atomic | rename file |
| AFERO-019 | `atomic::TestAFERO019` | atomic | rename directory tree |
| AFERO-020 | `atomic::TestAFERO020` | atomic | shared file state |
| AFERO-021 | `atomic::TestAFERO021` | atomic | independent offsets |
| AFERO-022 | `atomic::TestAFERO022` | atomic | closed handle |
| AFERO-023 | `atomic::TestAFERO023` | atomic | double close |
| AFERO-024 | `atomic::TestAFERO024` | atomic | readonly openfile write rejected |
| AFERO-025 | `atomic::TestAFERO025` | atomic | readonly mutators |
| AFERO-026 | `atomic::TestAFERO026` | atomic | directory sorted |
| AFERO-027 | `atomic::TestAFERO027` | atomic | directory cursor |
| AFERO-028 | `atomic::TestAFERO028` | atomic | readdir regular file |
| AFERO-029 | `atomic::TestAFERO029` | atomic | basepath read |
| AFERO-030 | `atomic::TestAFERO030` | atomic | basepath create |
| AFERO-031 | `atomic::TestAFERO031` | atomic | basepath escape |
| AFERO-032 | `atomic::TestAFERO032` | atomic | nested basepath |
| AFERO-033 | `atomic::TestAFERO033` | atomic | cow read does not copy |
| AFERO-034 | `atomic::TestAFERO034` | atomic | cow create overlay |
| AFERO-035 | `atomic::TestAFERO035` | atomic | cache populates |
| AFERO-036 | `integration::TestAFERO036` | integration | cow copyup write isolates base |
| AFERO-037 | `integration::TestAFERO037` | integration | cow truncate isolates base |
| AFERO-038 | `integration::TestAFERO038` | integration | cow chmod copyup |
| AFERO-039 | `integration::TestAFERO039` | integration | cow chtime copyup |
| AFERO-040 | `integration::TestAFERO040` | integration | cow base rename fails |
| AFERO-041 | `integration::TestAFERO041` | integration | cow base remove fails |
| AFERO-042 | `integration::TestAFERO042` | integration | cow remove reveals base |
| AFERO-043 | `integration::TestAFERO043` | integration | cow union deduplicates |
| AFERO-044 | `integration::TestAFERO044` | integration | cow union directory cursor |
| AFERO-045 | `integration::TestAFERO045` | integration | cow mkdirall existing base |
| AFERO-046 | `integration::TestAFERO046` | integration | cow create under base dir |
| AFERO-047 | `integration::TestAFERO047` | integration | cow overlay shadows base |
| AFERO-048 | `integration::TestAFERO048` | integration | cow overlay file shadows base dir |
| AFERO-049 | `integration::TestAFERO049` | integration | cow missing open |
| AFERO-050 | `integration::TestAFERO050` | integration | cache zero keeps hit |
| AFERO-051 | `integration::TestAFERO051` | integration | cache stale refresh |
| AFERO-052 | `integration::TestAFERO052` | integration | cache create writes both |
| AFERO-053 | `integration::TestAFERO053` | integration | cache openfile writes both |
| AFERO-054 | `integration::TestAFERO054` | integration | cache mkdirall writes both |
| AFERO-055 | `integration::TestAFERO055` | integration | cache remove writes both |
| AFERO-056 | `integration::TestAFERO056` | integration | cache rename writes both |
| AFERO-057 | `integration::TestAFERO057` | integration | cache local file |
| AFERO-058 | `integration::TestAFERO058` | integration | basepath mutator roundtrip |
| AFERO-059 | `integration::TestAFERO059` | integration | readonly over basepath |
| AFERO-060 | `integration::TestAFERO060` | integration | cow with readonly base |
| AFERO-061 | `integration::TestAFERO061` | integration | open handle survives rename |
| AFERO-062 | `integration::TestAFERO062` | integration | open handle survives remove |
| AFERO-063 | `integration::TestAFERO063` | integration | concurrent distinct paths |
| AFERO-064 | `integration::TestAFERO064` | integration | concurrent independent readers |
| AFERO-065 | `integration::TestAFERO065` | integration | interface signatures |
