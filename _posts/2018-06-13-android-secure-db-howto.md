---
layout: post
title: 안드로이드 앱의 Persistent data를 제대로 암호화해 보자! (2/2)
date: 2018-06-13
author: hwan
published: true
excerpt: 안드로이드에서 Room을 사용하여 Database를 암호화하는방법에 대해 설명합니다.
tags: android tip kotlin cipher security room
---
## 들어가기
[1부]({% post_url 2018-06-03-android-secure-sharedpref-howto %})에서는, KeyStore 를 사용해 Shared Preferences 를 암호화 하는 법에 대해 알아봤습니다. 그리고 이 글에서는 [Room](https://developer.android.com/topic/libraries/architecture/room)을 사용한 Database 를 암호화 하는 방법에 대해 설명합니다.

2018년 현재, 안드로이드 자체에서 데이터베이스를 암호화하는 기능을 제공해 주진 않습니다. 따라서 오픈 소스 프로젝트인 [SQLCipher](https://github.com/sqlcipher/android-database-sqlcipher), [SafeRoom](https://github.com/commonsguy/cwac-saferoom) 의 사용법 위주로 설명할 예정입니다. 또한 [KeyStore 에 대칭키를 생성](https://developer.android.com/training/articles/keystore#SupportedKeyGenerators)하는 기능은 API Level 23 이후에서만 가능하며, SQLCipher 가 Android KeyStore 를 지원하지 않고 있습니다.

이로 인해 1부에서 소개한 키 암호화 메커니즘으로 보호한 별도의 키를 디스크 어딘가에 저장해 두고, 필요할 때만 복호화 해서 쓴 다음 복호화된 내용을 지우는 방식으로 구현해야 합니다. 하지만 이런 방식으로 사용하는 키는 메모리에 순간적으로 남기 때문에 좋은 공격 표면([Attack surface](https://en.wikipedia.org/wiki/Attack_surface)) 이 됩니다. 그 이유도 함께 다뤄 보겠습니다.

SqlCipher team 에서 하루라도 빨리 현재의 `char[]` 형식의 passphrase 를 입력받는 대신, JCA 를 사용해 암호화하는 데이터베이스를 구현하길 기대해 봅시다.

## SqlCipher
1부에서 보여드렸다시피 internal storage 에 저장한 데이터는 결코 안전하지 않습니다. 파일 DB 인 Sqlite 데이터는 포맷을 모르면 어차피 볼 수 없을테니 조금 다르지 않을까요? **그렇지 않다**는 것을 다음 예에서 보여드리겠습니다. 루팅한 디바이스에서 `adb pull` 명령으로 sqlite3 데이터베이스를 추출 후 내용을 열어보면 다음과 같습니다.

```shell
$ hexdump -vC secure_database.sqlite3
00000000  53 51 4c 69 74 65 20 66  6f 72 6d 61 74 20 33 00  |SQLite format 3.|
00000010  10 00 02 02 00 40 20 20  00 00 00 02 00 00 00 04  |.....@  ........|
00000020  00 00 00 00 00 00 00 00  00 00 00 04 00 00 00 04  |................|
00000030  00 00 00 00 00 00 00 04  00 00 00 01 00 00 00 00  |................|
00000040  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |................|
00000050  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 02  |................|
00000060  00 2e 01 5a 0d 0f 95 00  02 0e a9 00 0e a9 0f c9  |...Z............|
00000070  0e 6f 0e 6f 00 00 00 00  00 00 00 00 00 00 00 00  |.o.o............|
...
00000d30  00 00 00 00 00 82 37 03  07 17 57 57 01 83 4d 74  |......7...WW..Mt|
00000d40  61 62 6c 65 73 71 6c 69  74 65 62 72 6f 77 73 65  |ablesqlitebrowse|
00000d50  72 5f 72 65 6e 61 6d 65  5f 63 6f 6c 75 6d 6e 5f  |r_rename_column_|
00000d60  6e 65 77 5f 74 61 62 6c  65 73 71 6c 69 74 65 62  |new_tablesqliteb|
00000d70  72 6f 77 73 65 72 5f 72  65 6e 61 6d 65 5f 63 6f  |rowser_rename_co|
00000d80  6c 75 6d 6e 5f 6e 65 77  5f 74 61 62 6c 65 05 43  |lumn_new_table.C|
00000d90  52 45 41 54 45 20 54 41  42 4c 45 20 60 73 71 6c  |REATE TABLE `sql|
00000da0  69 74 65 62 72 6f 77 73  65 72 5f 72 65 6e 61 6d  |itebrowser_renam|
00000db0  65 5f 63 6f 6c 75 6d 6e  5f 6e 65 77 5f 74 61 62  |e_column_new_tab|
00000dc0  6c 65 60 20 00 00 00 00  00 00 00 00 00 00 00 09  |le` ............|
...
```
**\[리스트 1\]** Internal storage 에 저장된 SQLite3 database 를 dump 한 결과.

역시 기대했던대로 데이터가 하나도 암호화되어 있지 않은 것을 확인할 수 있습니다. 그렇다면 가장 간단한 방법은 [`SQLiteDatabase`](https://android.googlesource.com/platform/frameworks/base/+/master/core/java/android/database/sqlite/SQLiteDatabase.java#77) 클래스를 확장하는 일일 텐데요, 문제는 이 클래스가 `final` 로 상속 불가능하게 되어 있단 점입니다. 이 때문에 암호화된 `SQLiteDatabase` 구현체는  이 클래스 및 이 클래스에 강하게 결합되어 있는 [`SQLiteOpenHelper`](https://android.googlesource.com/platform/frameworks/base/+/master/core/java/android/database/sqlite/SQLiteOpenHelper.java#55) 를 온전히 쓸 수 없다는 문제가 있습니다. 즉, 바닥부터 새로 만들어야 하는 상황인데요, 다행히도 Zetetic 사에서 만든 [SQLCipher for Android](https://github.com/sqlcipher/android-database-sqlcipher) 는 이 문제를 모두 해결해 주는 고마운 오픈 소스 프로젝트입니다.

SqlCipher 의 사용법은 기존의 SQLiteDatabase 에 의존하던 로직들의 import namespace 만 바꿔주면 되도록 구현되어 있어 마이그레이션 비용도 거의 들지 않습니다.

```java
// 안드로이드에서 제공해 주는 SQLiteDatabase 클래스명
import android.database.sqlite.SQLiteDatabase;

// SqlCipher 에서 제공해 주는 SQLiteDatabase 클래스명
import net.sqlcipher.database.SQLiteDatabase;

// 프로그램 시작시 native library 를 로드해줘야 한다.
class MyApplication extends android.app.Application {
    @Override public void onCreate() {
        super.onCreate();
        net.sqlcipher.database.SQLiteDatabase.loadLibs(this);
    }
}
```
**\[리스트 2\]** android SQLiteDatabase 에서 SqlCipher SQLiteDatabase 로 마이그레이션 하기

물론 두 클래스는 전혀 타입 호환되지 않지만, `net.sqlcipher.database.SQLiteDatabase` 의 모든 메소드 및 field의 signature 가 기본 `android.database.sqlite.SQLiteDatabase` 와 같기 때문에 이런 변경이 가능합니다. SqlCipher 개발팀의 수고에 박수를 보냅니다.

## Room
Room 은 SQL 을 객체로 매핑해 주는 도구입니다. Room 을 이용해 데이터베이스를 열 때는 보통 아래와 같은 코드를 사용합니다.

```kotlin
object Singletons {
    val db: DataSource by lazy {
        Room.databaseBuilder(appContext, DataSource::class.java, "secure_database")
            .build()
    }
}

abstract class DataSource: RoomDatabase() {
    abstract fun userProfileDao(): UserProfileDao
}

// 클라이언트 코드에서 아래와 같이 호출
val userProfile: UserProfile = Singletons.db.userProfileDao().findUserByUid(userId)
```
**\[리스트 3\]** Room database 의 정의 및 활용

Sqlite 의 기본 동작은 파일 데이터베이스에 단순 Read 및 Write 만 합니다. 따라서 데이터베이스 접근시 암호화/복호화 동작을 하는 callback 을 주입해야 데이터베이스를 암호화 할 수 있습니다. 그리고 `RoomDatabase.Builder` 클래스는 데이터베이스를 열때 우리가 주입한 일을 할 수 있는 [hook method](https://android.googlesource.com/platform/frameworks/support/+/master/room/runtime/src/main/java/android/arch/persistence/room/RoomDatabase.java#343)(`openHelperFactory`) 를 제공해 주고 있습니다. 다음 코드를 살펴봅시다.

```java
class RoomDatabase.Builder {
    class Builder {
        /**
        * Sets the database factory. If not set, it defaults to {@link FrameworkSQLiteOpenHelperFactory}.
        */
        @NonNull
        public Builder<T> openHelperFactory(@Nullable SupportSQLiteOpenHelper.Factory factory)
    }
}

interface SupportSQLiteOpenHelper {
    /**
     * Create and/or open a database that will be used for reading and writing.
     */
    SupportSQLiteDatabase getWritableDatabase();

    /**
     * Create and/or open a database. This will be the same object returned by {@link #getWritableDatabase}.
     */
    SupportSQLiteDatabase getReadableDatabase();

    /**
     * Factory class to create instances of {@link SupportSQLiteOpenHelper} using {@link Configuration}.
     */
    interface Factory {
        /**
         * Creates an instance of {@link SupportSQLiteOpenHelper} using the given configuration.
         */
        SupportSQLiteOpenHelper create(Configuration configuration);
    }
}
```
**\[리스트 4\]** Room builder 의 `SupportSQLiteOpenHelper` 주입 메소드 및 `SupportSQLiteOpenHelper.Factory` 인터페이스 정의

설명을 최대한 간소하게 하기 위해 관심가질 필요 없는 코드 및 코멘트는 모두 제외했습니다. 아무튼 [`SupportSQLiteOpenHelper`](https://android.googlesource.com/platform/frameworks/support/+/master/persistence/db/src/main/java/android/arch/persistence/db/SupportSQLiteOpenHelper.java#381) 구현체를 주입하면 뭔가 데이터베이스 작업 이전에 우리의 로직을 실행할 수 있을 것 같습니다.

사실 이 인터페이스의 핵심은 바로 [`getWritableDatabase()`](https://android.googlesource.com/platform/frameworks/support/+/master/persistence/db/src/main/java/android/arch/persistence/db/SupportSQLiteOpenHelper.java#79), [`getReadableDatabase()`](https://android.googlesource.com/platform/frameworks/support/+/master/persistence/db/src/main/java/android/arch/persistence/db/SupportSQLiteOpenHelper.java#99) 구현입니다. javadoc 에도 있지만 두 메소드로 반환하는 인스턴스는 같아야 하며 또한 암호화를 지원해야 한다는 것을 알 수 있습니다.

결국 우리 목표는 Room 과 데이터베이스 암호화 로직을 연결해 주는 [`SupportSQLiteDatabase` 구현체](https://android.googlesource.com/platform/frameworks/support/+/master/persistence/db/src/main/java/android/arch/persistence/db/SupportSQLiteDatabase.java)를 만드는 것임을 알 수 있습니다. 이 인터페이스는 규모가 제법 크기 때문에 이게 만만한 일이 아님을 직감하실 수 있을 겁니다.

## saferoom 도입으로 SupportSQLiteDatabase 인터페이스 구현체 사용하기
앞서 살펴봤듯 `SupportSQLiteDatabase` 구현에는 상당한 노력이 필요하단 것을 알 수 있습니다. 그런데 고맙게도 [saferoom](https://github.com/commonsguy/cwac-saferoom) 이라는 오픈 소스 프로젝트가 우리의 귀찮음을 잘 해결해 주고 있습니다. saferoom 의 `SupportSQLiteOpenHelper` 구현체를 간단히 살펴보면 아래와 같습니다.

```java
/**
 * SupportSQLiteOpenHelper.Factory implementation, for use with Room
 * and similar libraries, that supports SQLCipher for Android.
 */
public class SafeHelperFactory implements SupportSQLiteOpenHelper.Factory {
    private final char[] passphrase;

    public SafeHelperFactory(final char[] passphrase) {
        this.passphrase = passphrase;
    }

    @Override
    public SupportSQLiteOpenHelper create(final SupportSQLiteOpenHelper.Configuration configuration) {
        return(new com.commonsware.cwac.saferoom.Helper(configuration.context,
            configuration.name, configuration.version, configuration.callback,
            this.passphrase));
    }

    /**
     * NOTE: this implementation zeros out the passphrase after opening the database
     */
    @Override
    public SupportSQLiteDatabase getWritableDatabase() {
        SupportSQLiteDatabase result = delegate.getWritableSupportDatabase(passphrase);

        for (int i = 0; i < passphrase.length; i++) {
            passphrase[i] = (char) 0;
        }

        return(result);
    }

    /**
     * NOTE: this implementation delegates to getWritableDatabase(), to ensure that we only need the passphrase once
     */
    @Override
    public SupportSQLiteDatabase getReadableDatabase() {
        return getWritableDatabase();
    }
}

/**
 * SupportSQLiteOpenHelper implementation that works with SQLCipher for Android
 */
class Helper implements SupportSQLiteOpenHelper {
    final OpenHelper delegate;

    Helper(Context context, String name, int version, SupportSQLiteOpenHelper.Callback callback, char[] passphrase) {
        net.sqlcipher.database.SQLiteDatabase.loadLibs(context);
        this.delegate = createDelegate(context, name, version, callback);
        this.passphrase = passphrase;
    }

    abstract static class OpenHelper extends net.sqlcipher.database.SQLiteOpenHelper {
        SupportSQLiteDatabase getWritableSupportDatabase(char[] passphrase) {
            SQLiteDatabase db = super.getWritableDatabase(passphrase);

            return getWrappedDb(db);
        }
    }
}
```
**\[리스트 5\]** Saferoom 의 `SupportSQLiteOpenHelper` 구현체.

소스 코드를 보면 SQLiteDatabase 의 원래 요구사항을 만족하지 못하는 구현 부분도 보입니다만, 그래도 이 정도면 수고를 꽤 크게 덜 수 있어 훌륭합니다.

그리고 로직을 잘 보면 데이터베이스를 연 직후 암호로 넘겨준 `char[]` 배열을 [초기화 하는 코드](https://github.com/commonsguy/cwac-saferoom/blob/master/saferoom/src/main/java/com/commonsware/cwac/saferoom/Helper.java#L122)가 있다는 점입니다. 이것이 바로 이 문서의 서두에서 말했던 attack surface 를 최소화 하기 위한 구현입니다. 이 글의 주제에서 벗어난 내용이기에 여기서는 다루지 않습니다만, 궁금하신 분들은 [부록 1: in-memory attack 맛보기](#부록-1-in-memory-attack-맛보기)에서 확인하실 수 있습니다.

## SqlCipher + SafeRoom + Room 구현 및 코드 설명
이상으로 데이터베이스 암호화 전략에 대해 살펴봤습니다. 이 장에서는 실제로 연동하는 방법에 대해 다룹니다.

불행히도 2018년 현재 SqlCipher 는 Android KeyStore 를 지원하지 않고 있습니다. 그리고 인스턴스 생성에 쓸 비밀번호로 `CharArray` 가 필요한데, 이 값은 한번 정해지면 불변해야 합니다. 여기 사용할 키를 KeyStore 에 저장하면 문제를 깔끔하게 해결할 수 있을 것 같습니다. 하지만 1부에서 살펴봤듯이 하드웨어로 구현된 Android KeyStore 밖으로는 키가 절대로 노출되지 않는다고 합니다. 이 문제를 어떻게 해결해야 할까요?

먼저, SqlCipher 에 사용하기 위해 KeyStore 로 생성한 AES256 키의 내용을 한번 살펴봅시다.

```kotlin
val secretKey = with(KeyGenerator.getInstance("AES", "AndroidKeyStore"), {
    init(KeyGenParameterSpec.Builder(alias, 
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
        .setKeySize(256)
        .setBlockModes(KeyProperties.BLOCK_MODE_CBC)
        .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_PKCS7)
        .build())
    generateKey()
})

val keyInfo = with(KeyFactory.getInstance(privKey.getAlgorithm(), "AndroidKeyStore"), {
    factory.getKeySpec(privKey, KeyInfo::class.java)
})

println("Key algorithm   : " + secretKey.algorithm)
println("Key format      : " + secretKey.format)
println("Encoded key size: " + secretKey.encoded?.size)
println("Hardware-backed : " + keyInfo.isInsideSecureHardware)

// 실행 결과
Key algorithm   : AES
Key format      : null
Encoded key size: null
Hardware-backed : true
```
**\[리스트 6\]** AndroidKeyStore 에 저장한 Key 는 어플리케이션에서 직접 쓸 수 없다.

저희가 보유중인 개발 시료 Nexus 5 에서 실행한 결과 위와 같이 나타났습니다. `secretKey.encoded` 의 값이 메모리에 있다면 이 값을 SqlCipher 생성자에 넘겨줄 수 있겠지만 값이 `null` 이네요. 보안 측면에서는 다행일 지 모르지만 우리 구현에서는 쓸 수 없으니 문제입니다. 그래서 별 수 없이 임의로 키를 만들고([`AndroidAesHelper#generateRandomKey()`](https://gist.github.com/FrancescoJo/b306925d245f095c68655c4c40bb38f8#file-androidaescipherhelper-kt-L149)), 1부에서 소개했던 [`AndroidRsaCipherHelper`](https://gist.github.com/FrancescoJo/b8280cff14f1254f2185a9c2e927565e) 를 이용해 암호화한 값을 Shared Preferences에 저장하는 식으로 구현해 봅시다.

```kotlin
val settingsPrefs = appContext.getSharedPreferences("app_settings", Context.MODE_PRIVATE)
val settings = SecureSharedPreferences.of(settingsPrefs)
val dbPass = with(settings, {
    /*
     * String.toCharArray() 같은 함수를 쓰면 로직이 좀더 간단해지지만, JVM 에서의 String은
     * Immutable 하기 때문에 GC 이전에는 지울 방법이 없으므로 attack surface 가 더 오랫동안
     * 노출되는 부작용이 있다. 따라서 key의 plaintext 는 가급적 String 형태로 저장하면 안된다.
     */
    var savedDbPass = getString("DB_PASSPHRASE", "")
    if (savedDbPass.isEmpty()) {
        // KeyStore 에 저장해도 SqlCipher 가 써먹질 못하니 그냥 1회용 키 생성 용도로만 활용한다.
        val secretKey = AndroidAesCipherHelper.generateRandomKey(256)
        // String 생성자 사용: 이 문자열은 heap 에 저장된다.
        savedDbPass = String(Base64.encode(secretKey, Base64.DEFAULT))
        putString("DB_PASSPHRASE",  AndroidRsaCipherHelper.encrypt(savedDbPass))
        // 메모리 내에 plaintext 형태로 존재하는 attack surface 를 소멸시켜 준다.
        secretKey.fill(0, 0, secretKey.size - 1)
    } else {
        // decrypt 메소드 내부에서 String 생성자 사용하므로 base64 인코딩된 plaintext 키는 heap 에 저장된다.
        savedDbPass = AndroidRsaCipherHelper.decrypt(savedDbPass)
    }

    val dbPassBytes = Base64.decode(savedDbPass, Base64.DEFAULT)
    /*
     * SqlCipher 내부에서는 이 char[] 배열이 UTF-8 인코딩이라고 가정하고 있다.
     * 그리고 UTF-8 인코딩에서는 byte range 의 char 는 1 바이트니까,
     * 아래 변환을 거치더라도 키 길이는 32 byte(256 bit)가 유지된다.
     *
     * UTF-8 인코딩에서는 32 글자 != 32 바이트가 아님에 항상 유의해야 한다!
     */
    CharArray(dbPassBytes.size, { i -> dbPassBytes[i].toChar() })
})
```
**\[리스트 7\]** 암호화한 SqlCipher 용 passphrase 를 사용하는 방법.

위 코드를 사용해 `char[]` 타입의 값 `dbPass` 를 얻을 수 있습니다. *리스트 7*을 이용해 얻은 `dbPass`를 아래 코드에 사용하면 SqlCipher - SafeRoom - Room 의 연동이 끝납니다.

```kotlin
val dataSource = Room.databaseBuilder(_instance, DataSource::class.java, "secure_database")
                     .openHelperFactory(SafeHelperFactory(dbPass))
                     .build()
// 메모리 내에 plaintext 형태로 존재하는 attack surface 를 소멸시켜 준다.
dbPass.fill('0', 0, dbPass.size - 1)
```
**\[리스트 8\]** SqlCipher - SafeRoom - Room 연동하기

위 코드에서 볼 수 있듯, 임의로 저장한 키를 Base64 인코딩으로 변환, 그리고 그것을 다시 `CharArray` 로 변환하는 과정에서 key 가 메모리에 존재해야 하는 순간이 있습니다. 이 구간을 바로 공격 표면(attack surface) 이라고 합니다. 

JVM 단에서 넘겨주는 Passphrase 를 SqlCipher 내부에서 native 로 어떻게 처리하고 있는지는 [SqlCipher SQLiteDatabase 구현](https://github.com/sqlcipher/android-database-sqlcipher/blob/master/android-database-sqlcipher/src/main/cpp/net_sqlcipher_database_SQLiteDatabase.cpp#L97) 및 [SqlCipher crypto 구현](https://github.com/sqlcipher/sqlcipher/blob/master/src/crypto.c#L434) 에서 확인할 수 있습니다.

## 결과 확인하기
`SafeHelperFactory` 를 주입한 Room database 파일을 추출 후 `hexdump` 로 확인해 보겠습니다.

```shell
hwan@ubuntu:~$ hexdump -vC secure_database.sqlite3
00000000  8c 0d 04 07 03 02 11 eb  a4 18 33 4f 93 e8 ed d2  |..........3O....|
00000010  e9 01 21 d7 49 df 25 9a  f4 1d c7 1e ff 2d b0 13  |..!.I.%......-..|
00000020  fc 17 9b 4b b2 1c a3 1d  7d 1d 69 76 b1 ea ec e8  |...K....}.iv....|
00000030  1f 50 e4 c4 6c 50 e6 82  58 27 b9 fe 85 21 27 99  |.P..lP..X'...!'.|
00000040  ec 54 53 ba 32 c6 59 09  b4 30 65 39 a0 75 3e c4  |.TS.2.Y..0e9.u>.|
00000050  b8 f7 ea 47 14 df c4 f0  7c be 9f 62 26 49 1c b2  |...G....|..b&I..|
00000060  0f 63 00 7a 09 7e 33 e0  43 2b eb ea 80 21 bb 5d  |.c.z.~3.C+...!.]|
00000070  5c 04 ff 57 a3 a3 7f c2  19 42 b9 67 6c e3 d5 c8  |\..W.....B.gl...|
...
00000d30  c1 f3 93 1f 4e 5b 6a 70  39 c2 e9 2c 3e 8f 7e ff  |....N[jp9..,>.~.|
00000d40  73 3a 9a 39 0d 8a 1a 3e  6b d4 5b de 1f 6d c4 b8  |s:.9...>k.[..m..|
00000d50  fb 62 3e 21 09 0a 31 20  37 5d 8d 0a 39 6d 35 31  |.b>!..1 7]..9m51|
00000d60  26 d6 b0 22 41 7e 6c 54  7d 77 22 ba 1b f3 cf 5a  |&.."A~lT}w"....Z|
00000d70  e5 47 97 76 f0 89 e5 98  b3 37 3c 8d 43 af 0e b9  |.G.v.....7<.C...|
00000d80  18 74 fd f5 2a 41 d8 b1  d9 70 32 0b 5c 93 4b 0d  |.t..*A...p2.\.K.|
00000d90  bc 60 4c 25 9a ec 53 23  90 60 b2 52 a8 a1 b1 87  |.`L%..S#.`.R....|
00000da0  f3 3e 03 3e ac 0a 75 a0  61 d8 bd 07 b8 5a 48 66  |.>.>..u.a....ZHf|
00000db0  57 85 13 ac 04 26 55 30  34 46 57 bf 8b 42 c6 2d  |W....&U04FW..B.-|
00000dc0  9e 82 a2 df 77 bb b3 2e  96 43 70 23 23 03 df 1d  |....w....Cp##...|
...
```
**\[리스트 9\]** Internal storage 에 저장된 SQLite3 database 를 dump 한 결과. *리스트 1*과 비교해 보자.

이로서 오픈 소스의 힘을 빌려 우리 앱의 데이터베이스를 비교적 간편하게 암호화 할 수 있음을 알 수 있습니다.

## 맺으며
이로서 Persistent data 암호화에 대한 설명을 마칩니다. Android KeyStore 가 API Level 23 이상의 기기에서만 100% 동작한다는 점은 2018년 현재까지는 큰 단점입니다. 하지만 사소한 데이터라 하더라도 보안의 중요성은 날로 강조되고 있습니다. 따라서 빠르던 늦던 고객 데이터 암호화에 투자해야 할 순간이 다가온다는 점은 변하지 않습니다.

언젠가는 적용해야 할 고객 데이터 보호의 순간에, 이 글이 여러분의 앱의 보안에 조금이나마 도움이 된다면 좋겠습니다.

## 부록 1: in-memory attack 맛보기
앞서 계속 반복해서 설명드렸던 메모리 내의 attack surface 를 찾아내는 방법을 간단히 설명해 보겠습니다. 잘 지키려면 잘 공격하는 법을 알아야 하므로 알아두면 좋지 않을까요? 그리고 일반적인 앱 개발과는 다소 동떨어진 이 장의 내용이 이해되지 않으신다면 한줄요약한 **메모리 내부의 값도  때로는 안전하지 않을 수 있다** 는 한마디만 기억해 두시면 됩니다. 모든 데모는 LG Nexus 5(Hammerhead), 시스템 버전 6.0.1(M) 에서 실행한 결과며 시스템마다 약간의 차이는 있을 수 있습니다.

마켓에 출시한 앱들은 `debuggable:false` 가 설정된 상태이므로 힙 덤프를 바로 뜰 수는 없습니다. 그런데 어떻게 in-memory attack 이 가능할까요? 다음 리스트는 디버그 불가능한 앱의 힙 덤프를 시도할 때 보안 정책 위반 오류가 발생함을 보여줍니다.

```shell
hwan@ubuntu:~$ adb shell ps | grep "com.securecompany.secureapp"
USER      PID   PPID  VSIZE   RSS    WCHAN               PC  NAME
u0_a431   25755 208   1700384 100888 sys_epoll_ 00000000 S   com.securecompany.secureapp

hwan@ubuntu:~$ adb shell am dumpheap 25755 "/data/local/tmp/com.securecompany.secureapp.heap"
java.lang.SecurityException: Process not debuggable: ProcessRecord{b6f96fc 25755:com.securecompany.secureapp/u0_a431}
	at android.os.Parcel.readException(Parcel.java:1620)
	at android.os.Parcel.readException(Parcel.java:1573)
	at android.app.ActivityManagerProxy.dumpHeap(ActivityManagerNative.java:4922)
	at com.android.commands.am.Am.runDumpHeap(Am.java:1248)
	at com.android.commands.am.Am.onRun(Am.java:377)
	at com.android.internal.os.BaseCommand.run(BaseCommand.java:47)
	at com.android.commands.am.Am.main(Am.java:100)
	at com.android.internal.os.RuntimeInit.nativeFinishInit(Native Method)
	at com.android.internal.os.RuntimeInit.main(RuntimeInit.java:251)
```
**\[리스트 10\]** `debuggable=false` 설정된 앱의 힙 덤프 시도시 발생하는 예외(SecurityException)

SuperUser 는 가능할까요? SuperUser 권한으로 앱을 강제로 디버그 가능한 상태로 시작해 보도록 하겠습니다.

```shell
hwan@ubuntu:~$ adb shell 

32|shell@hammerhead:/ $ su
1|root@hammerhead:/ \# am start -D -n "com.securecompany.secureapp/MainActivity" && exit
Starting: Intent { cmp=com.securecompany.secureapp/MainActivity }

hwan@ubuntu:~$ \# adb shell ps | grep "com.securecompany.secureapp"
USER      PID   PPID  VSIZE   RSS    WCHAN               PC  NAME
u0_a431   27482 211   1700384 100888 sys_epoll_ 00000000 S   com.securecompany.secureapp

hwan@ubuntu:~$ adb forward tcp:12345 jdwp:27482
hwan@ubuntu:~$ netstat -an | grep 12345                                                                              
tcp4       0      0  127.0.0.1.12345         *.*                    LISTEN     
hwan@ubuntu:~$ jdb -connect com.sun.jdi.SocketAttach:hostname=127.0.0.1,port=12345
java.net.SocketException: Connection reset
	at java.net.SocketInputStream.read(SocketInputStream.java:210)
	at java.net.SocketInputStream.read(SocketInputStream.java:141)
	at com.sun.tools.jdi.SocketTransportService.handshake(SocketTransportService.java:130)
	at com.sun.tools.jdi.SocketTransportService.attach(SocketTransportService.java:232)
	at com.sun.tools.jdi.GenericAttachingConnector.attach(GenericAttachingConnector.java:116)
	at com.sun.tools.jdi.SocketAttachingConnector.attach(SocketAttachingConnector.java:90)
	at com.sun.tools.example.debug.tty.VMConnection.attachTarget(VMConnection.java:519)
	at com.sun.tools.example.debug.tty.VMConnection.open(VMConnection.java:328)
	at com.sun.tools.example.debug.tty.Env.init(Env.java:63)
	at com.sun.tools.example.debug.tty.TTY.main(TTY.java:1082)

Fatal error:
Unable to attach to target VM.
```
**\[리스트 12\]** SuperUser 권한으로도도 Java 디버거를 붙일 수 없다.

다행히도 `debuggable=false` 로 릴리즈한 앱은 자바 디버거(`jdb`)를 붙일 수 없으니 프로그램 실행을 매우 정밀하게 제어할 수는 없다는 것을 알 수 있습니다(`debuggable=true` 설정된 앱에 위 과정을 실행하면 어떤 일이 벌어지는지 직접 확인해 보세요!).

하지만 안드로이드의 앱은 'linux process' 에서 실행되므로 SuperUser 권한으로 process 메모리 전체 dump를 뜨는 것은 막을 수 없습니다. 정공법으로는 `/proc/PID/maps` 의 내용을 분석하면 됩니다만 제가 안드로이드를 깊게 알고 있는 것은 아니라, 어느 영역이 dalvik heap 인지를 알아낼 수 없었습니다. 이 때문에 프로세스 메모리를 통째로 떠서 내용을 헤집어보는 방식으로 공격해 보겠습니다. 여담입니다만, 데모를 위해 공격한 앱은 `dumpsys` 명령으로 확인해보니 약 6MiB 의 Java heap 을 쓰고 있는데요, 이 크기를 줄이면 줄일 수록 공격이 더욱 수월할 겁니다.

아래 데모에서는 안드로이드 기기용(`arm-linux-gnueabi`)으로 컴파일한 `gdb` 를 미리 설치한 결과를 보여드리고 있습니다. 참고로 여기 보이는 [heap] 은 아쉽지만 native heap 이므로 우리 공격 목표는 아닙니다.

```shell
1|root@hammerhead:/ \# cd /proc/27482
1|root@hammerhead:/proc/27482 \# cat maps
12c00000-12e07000 rw-p 00000000 00:04 8519       /dev/ashmem/dalvik-main space (deleted)
...
b7712000-b771f000 rw-p 00000000 00:00 0 [heap]
bee86000-beea7000 rw-p 00000000 00:00 0 [stack]
ffff0000-ffff1000 r-xp 00000000 00:00 0 [vectors]

1|root@hammerhead:/proc/27482 \# ifconfig
wlan0     Link encap:Ethernet
          inet addr:192.168.12.117
          inet6 addr: fe80::8e3a:e3ff:fe5f:64c9/64

1|root@hammerhead:/proc/27482 \# gdbserver –attach :12345 27482
Attached; pid = 27482
Listening on port 12345
```
**\[리스트 13\]** SuperUser 권한으로 `gdbserver` 실행.

```shell
hwan@ubuntu:~$ adb forward tcp:23456 tcp:12345
hwan@ubuntu:~$ netstat -an | grep 23456
tcp4       0      0  127.0.0.1.23456         *.*                    LISTEN     
```
**\[리스트 14\]** 로컬 포트 23456 으로 원격 포트 12345 를 연결하는 과정.

이제 모든 준비가 끝났습니다. 개발 기기에서 `gdb`로 원격 프로세스에 접근한 뒤, 메모리를 덤프해 봅시다.

```
hwan@ubuntu:~$ ./gdb
(gdb) target remote 192.168.12.117:12345
Remote debugging using 192.168.12.117:12345
0xb6f92834 in ?? ()
(gdb) dump memory /tmp/com.securecompany.secureapp.heap 0x12c00000 0xb771f000
(gdb)
``` 
**\[리스트 15\]** `gdb` 로 메모리를 덤프하는 과정.

덤프한 힙 덤프 파일 속에 있을지도 모르는 문자열을 검색해 봅시다. 그 전에 잠시, 데이터베이스에 사용할 키를 어떻게 처리했었나 되새겨 볼까요?

```kotlin
    if (savedDbPass.isEmpty()) {
        // ...
        // String 생성자 사용: 이 문자열은 heap 에 저장된다.
        savedDbPass = String(Base64.encode(secretKey, Base64.DEFAULT))
    } else {
        // decrypt 메소드 내부에서 String 생성자 사용하므로 base64 인코딩된 plaintext 키는 heap 에 저장된다.
        savedDbPass = AndroidRsaCipherHelper.decrypt(savedDbPass)
    }
```
**\[리스트 16\]** Base64 인코딩을 처리하기 위한 임시 String 생성 과정.

우리 로직은 256 비트의 키를 Base64 변환해서 디스크에 저장합니다. 그리고 256비트의 byte array 를 base64 변환한 결과는 (4 * (256 / 3)) / 8 = 42.66 바이트 -> 4의 배수여야 하므로 44바이트입니다. 약 1.34 바이트의 pad 를 맞추기 위해 문자열의 끝에 `=` 가 최소 1글자 이상은 있을 겁니다. 한번 찾아봅시다.

```shell
hwan@ubuntu:~$ strings /tmp/com.securecompany.secureapp.heap
...
/masterkey
...
user_0/.masterkey
em_s
1337
...
```
**\[리스트 17\]** `strings` 명령을 사용한 힙 덤프 파일내의 문자열 검색

의외로 `=` 나 `==` 로 끝나는 문자열이 발견되지 않습니다. 하지만 안심하기는 이릅니다. 이건 단순히 (공격자의 입장에서) 운이 나빠서 발견되지 않은 것일 뿐입니다. 우리가 원하는 어떤 '순간' 에 힙 덤프 명령을 내리지 않았기 때문에 그렇습니다. 우리의 구현은 attack surface 를 매우 짧은 시간동안만 메모리에 노출하기 때문에 이 순간이 짧으면 짧을 수록, 디바이스의 성능이 좋으면 좋을 수록 순간을 잡아내기가 더욱 어려워집니다. 즉, 이 문서에서 보여드린 방식으로 `CharArray` 의 내용을 아주 짧은 시간 동안만 사용하고 지워버리면 내용을 탈취하기 굉장히 어렵습니다. 하지만 안심하기는 이릅니다. nano-time 단위로 앱을 실행할 수 있는 환경을 가진 **국가급** 공격자는 여전히 있기 때문입니다.

그리고 이 방법은 루팅하지 않은 기기에서는 절대 재현이 불가능하므로 [루팅되지 않은 환경일 경우에만 실행](https://github.com/scottyab/rootbeer) 가능하도록 한다던가 하는 방식까지 더한다면 공격자가 더욱 우리 앱을 뚫기 힘들 겁니다.

여담입니다만 독자 여러분들 중 GameGuardian 처럼 다른 게임의 메모리값을 마구 바꾸는 앱이 어떻게 동작하나 궁금하신 분들도 있을 겁니다. 그런 류의 앱들도 바로, 이 장에서 설명했던 방식으로 동작합니다.

장황했던 이 장의 내용을 한줄로 요약하면 **Android KeyStore 로 보호하지 않은 키는 많은 수고를 들이면 뚫을 수 있다**고 할 수 있습니다.

## 부록 2: SQLite database 의 UPDATE / DELETE 구현 특성
SQLite3 의 구현특성상, UPDATE / DELETE 시에 이전 레코드의 값이 남아있는 경우가 있습니다. 암호화 했으니 좀더 안전하다곤 하지만 찌거기 값을 굳이 남겨둬서 공격자에게 더 많은 힌트를 제공할 필요도 없습니다.

이 문서는 암호화 구현에만 초점을 맞췄기 때문에 상세하게 다루진 않습니다만, LINE Tech blog에 소개된 [True delete](https://engineering.linecorp.com/ko/blog/detail/64) 는 이 문제를 해결하기 위한 방법을 제시하고 있으므로 그 문서도 한번 읽어보시길 권합니다.

## 더 보기
  - [SQLCipher](https://github.com/sqlcipher/android-database-sqlcipher)
  - [SafeRoom](https://github.com/commonsguy/cwac-saferoom)
  - [Android SQLite3 True delete - by LINE tech blog](https://engineering.linecorp.com/ko/blog/detail/64)
  - [Difference between java.util.Random and java.security.SecureRandom](https://stackoverflow.com/questions/11051205/difference-between-java-util-random-and-java-security-securerandom)
  - [Attack surface on security measures](https://en.wikipedia.org/wiki/Attack_surface)
  - [AOSP: Debugging](https://source.android.com/devices/tech/debug/gdb)
  - [Rootbeer: Simple to use root checking Android library](https://github.com/scottyab/rootbeer)
