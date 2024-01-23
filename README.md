# wechat-avatar

自2022年3月InstructGPT问世至今，涌现了许多大语言模型，它们以超强的自然语言理解，代码生成、甚至工具使用的能力不断刷新我们的认知。然而这么久过去了，自己还不曾上手做过实验。所以趁此机会，以微信开放域聊天作为任务背景，来真正上手过一遍。至于为什么选择这个场景，首要原因当然是没有足够的资源跑预训练，只能做指令微调；其次涉及模型量化、部署以及连接微信，能够锻炼一下代码能力。

## 1. 数据处理

对于所有NLP任务，数据质量决定了模型的上限。

### 1.1 微信聊天记录导出

首先当然要将微信聊天数据导出制作指令微调数据集。具体的导出方法（移动端Android+Pc端Windows）在网上都有教程，此处就只做一下踩坑记录：

* 现版本的夜神模拟器(8.8.xx)不支持RE资源管理器，系统自带的Amaze也没有超级用户权限，无法访问根目录，可以使用雷电模拟器代替（有超级用户权限）。
* 不要使用模拟器的IMEI号，使用“1234567890ABCDEF”

解密后的EnMicroMsg.db文件如图：

![image-20230703210201527](https://s2.loli.net/2024/01/22/sG8KjPZYVkUelyq.png)

我们需要rcontact，userinfo，message这三个表，点击左上角依次导出为csv。

message表为所有的聊天记录，表格式如图：

![image-20230703210408684](https://s2.loli.net/2024/01/22/LrPZUn2cM9iOxk4.png)

需要用到的字段分别为：

**isSend**: 0代表对方发送，1代表自己发送

**createTime**: 消息对应时间戳

**talker**: 消息发送方，个人微信对应微信号，群聊为"xxx@chatroom"。微信号对应的微信名和备注可以在rcontact表中找到。

**content**: 消息内容

### 1.2 数据集制作

数据集制作是最重要的一步，既然是要克隆一个自己，就应该考虑自己在各种情况下做出什么样的响应。

### 1.2.1 各种聊天数据形式

聊天除了最基本的文本外，还有很多数据形式需要加以处理，形成自然语言的格式。

**引用**：

![image-20230705104426098](https://s2.loli.net/2024/01/22/F2fXPvZaSjpWYUT.png)

```xml
<msg>	
	<appmsg appid="" sdkver="0">
		<title>我没问我爸</title>
		<des />
		<type>57</type>
		<appattach>
			<cdnthumbaeskey />
			<aeskey></aeskey>
		</appattach>
		<refermsg>
			<type>1</type>
			<svrid>8763671344321550129</svrid>
			<fromusr>wxid_vwu99i8nzu8h22</fromusr>
			<chatusr />
			<displayname>??</displayname>
			<content>我妈说可以</content>
			<createtime>1687360045</createtime>
		</refermsg>
	</appmsg>
	<fromusername>wxid_vwu99i8nzu8h22</fromusername>
	<scene>0</scene>
	<appinfo>
		<version>1</version>
		<appname />
	</appinfo>
	<commenturl />
</msg>
```

直接取输入的内容

**Emoji**： 

![image-20230705111602970](https://s2.loli.net/2024/01/22/ya1QpbMJli8PD4u.png)

```[捂脸]
[捂脸]
```

保留原文

**外部链接**：

![image-20230705111707145](https://s2.loli.net/2024/01/22/C3nfA1jcKyuoeiV.png)

```xml
<msg><appmsg appid="wxcb8d4298c6a09bcb" sdkver="0"><title>凌晨四点起床，我见到了传说中的“接天莲叶无穷碧，映日荷花别样红”</title><des>UP主：张力视觉&#x0A;播放：2.5万</des><username></username><action>view</action><type>4</type><showtype>0</showtype><content></content><url>https://b23.tv/C2cjKiU?share_medium=android&amp;share_source=weixin&amp;bbid=XY8BB5F848CF28F07B1E21260E2BE11007ED6&amp;ts=1688043715309</url><lowurl></lowurl><forwardflag>0</forwardflag><dataurl></dataurl><lowdataurl></lowdataurl><contentattr>0</contentattr><streamvideo><streamvideourl></streamvideourl><streamvideototaltime>0</streamvideototaltime><streamvideotitle></streamvideotitle><streamvideowording></streamvideowording><streamvideoweburl></streamvideoweburl><streamvideothumburl></streamvideothumburl><streamvideoaduxinfo></streamvideoaduxinfo><streamvideopublishid></streamvideopublishid></streamvideo><canvasPageItem><canvasPageXml><![CDATA[]]></canvasPageXml></canvasPageItem><appattach><totallen>0</totallen><attachid></attachid><cdnattachurl></cdnattachurl><emoticonmd5></emoticonmd5><aeskey></aeskey><fileext></fileext><islargefilemsg>0</islargefilemsg></appattach><extinfo></extinfo><androidsource>2</androidsource><thumburl></thumburl><mediatagname></mediatagname><messageaction><![CDATA[]]></messageaction><messageext><![CDATA[]]></messageext><emoticongift><packageflag>0</packageflag><packageid></packageid></emoticongift><emoticonshared><packageflag>0</packageflag><packageid></packageid></emoticonshared><designershared><designeruin>0</designeruin><designername>null</designername><designerrediretcturl>null</designerrediretcturl></designershared><emotionpageshared><tid>0</tid><title>null</title><desc>null</desc><iconUrl>null</iconUrl><secondUrl>null</secondUrl><pageType>0</pageType><setKey>null</setKey></emotionpageshared><webviewshared><shareUrlOriginal></shareUrlOriginal><shareUrlOpen></shareUrlOpen><jsAppId></jsAppId><publisherId></publisherId></webviewshared><template_id></template_id><md5></md5><weappinfo><username></username><appid></appid><appservicetype>0</appservicetype><secflagforsinglepagemode>0</secflagforsinglepagemode><videopageinfo><thumbwidth>0</thumbwidth><thumbheight>0</thumbheight><fromopensdk>0</fromopensdk></videopageinfo></weappinfo><statextstr>GhQKEnd4Y2I4ZDQyOThjNmEwOWJjYg==</statextstr><musicShareItem><musicDuration>0</musicDuration></musicShareItem><finderLiveProductShare><finderLiveID></finderLiveID><finderUsername></finderUsername><finderObjectID></finderObjectID><finderNonceID></finderNonceID><liveStatus></liveStatus><appId></appId><pagePath></pagePath><productId></productId><coverUrl></coverUrl><productTitle></productTitle><marketPrice><![CDATA[0]]></marketPrice><sellingPrice><![CDATA[0]]></sellingPrice><platformHeadImg></platformHeadImg><platformName></platformName><shopWindowId></shopWindowId><flashSalePrice><![CDATA[0]]></flashSalePrice><flashSaleEndTime><![CDATA[0]]></flashSaleEndTime><ecSource></ecSource><sellingPriceWording></sellingPriceWording></finderLiveProductShare><finderOrder><appID></appID><orderID></orderID><path></path><priceWording></priceWording><stateWording></stateWording><productImageURL></productImageURL><products></products><productsCount><![CDATA[0]]></productsCount></finderOrder><finderShopWindowShare><finderUsername></finderUsername><avatar></avatar><nickname></nickname><commodityInStockCount></commodityInStockCount><appId></appId><path></path><appUsername></appUsername><query></query><liteAppId></liteAppId><liteAppPath></liteAppPath><liteAppQuery></liteAppQuery></finderShopWindowShare><findernamecard><username></username><avatar><![CDATA[]]></avatar><nickname></nickname><auth_job></auth_job><auth_icon>0</auth_icon><auth_icon_url></auth_icon_url></findernamecard><finderGuarantee><scene><![CDATA[0]]></scene></finderGuarantee><directshare>0</directshare><gamecenter><namecard><iconUrl></iconUrl><name></name><desc></desc><tail></tail><jumpUrl></jumpUrl></namecard></gamecenter><patMsg><chatUser></chatUser><records><recordNum>0</recordNum></records></patMsg><secretmsg><issecretmsg>0</issecretmsg></secretmsg><referfromscene>0</referfromscene><websearch><rec_category>0</rec_category><channelId>0</channelId></websearch></appmsg></msg>
```

输出：’[外部链接]凌晨四点起床，我见到了传说中的“接天莲叶无穷碧，映日荷花别样红”‘

**图片**：

![image-20230705111953936](https://s2.loli.net/2024/01/22/GYC7H3rfEbRowqN.png)

```xml
<msg><img cdnbigimgurl="null" hdlength="0" cdnhdheight="0" length="240962" cdnthumbaeskey="efd1f9b34175d24d77f16f647fd89735" md5="5a070c09ada3332b922d118b3cbffa8a" hevc_mid_size="240962" cdnhdwidth="0" cdnthumbwidth="120" cdnthumbheight="90" aeskey="efd1f9b34175d24d77f16f647fd89735" cdnmidwidth="0" cdnmidheight="0" cdnthumblength="5270" encryver="1" cdnmidimgurl="3057020100044b3049020100020401d7ac9402032f565d02040f40aa3d0204649d71b8042461646530666430622d316334342d346333352d383433642d356464613461626361656232020401150a020201000405004c51e500" cdnthumburl="3057020100044b3049020100020401d7ac9402032f565d02040f40aa3d0204649d71b8042461646530666430622d316334342d346333352d383433642d356464613461626361656232020401150a020201000405004c51e500" /></msg>
```

输出：’[手机图片]‘

**表情包**：

![image-20230705112257891](https://s2.loli.net/2024/01/22/p1oW5wdHX3IQDLS.png)

```
wxid_2tunsuqz1y1922:0:1:985158c85f6ba7d4a7edb77a8ff47cf8::0
```

输出：’[表情包]‘

**微信转账**：

![image-20230705112733972](https://s2.loli.net/2024/01/22/TsvKwt7ZoAJeInp.png)

```xml
<msg>
	<appmsg appid="" sdkver="">
		<title><![CDATA[微信转账]]></title>
		<des><![CDATA[收到转账1.00元。如需收钱，请点此升级至最新版本]]></des>
		<action />
		<type>2000</type>
		<content><![CDATA[]]></content>
		<url><![CDATA[https://support.weixin.qq.com/cgi-bin/mmsupport-bin/readtemplate?t=page/common_page__upgrade&text=text001&btn_text=btn_text_0]]></url>
		<thumburl><![CDATA[https://support.weixin.qq.com/cgi-bin/mmsupport-bin/readtemplate?t=page/common_page__upgrade&text=text001&btn_text=btn_text_0]]></thumburl>
		<lowurl />
		<extinfo />
		<wcpayinfo>
			<paysubtype>1</paysubtype>
			<feedesc><![CDATA[￥1.00]]></feedesc>
			<transcationid><![CDATA[-]]></transcationid>
			<transferid><![CDATA[-]]></transferid>
			<invalidtime><![CDATA[1687449272]]></invalidtime>
			<begintransfertime><![CDATA[1687362872]]></begintransfertime>
			<effectivedate><![CDATA[1]]></effectivedate>
			<pay_memo><![CDATA[]]></pay_memo>
			<receiver_username><![CDATA[wxid_2tunsuqz1y1922]]></receiver_username>
			<payer_username><![CDATA[]]></payer_username>
		</wcpayinfo>
	</appmsg>
</msg>
```

输出：’[微信转账]‘

**群公告**：

```
<msg>
    <appmsg appid="" sdkver="0">
        <type>87</type>
        <url>https://support.weixin.qq.com/cgi-bin/mmsupport-bin/readtemplate?t=page/common_page__upgrade&amp;btn_text=btn_text_0&amp;text=text008</url>
        <announcement><![CDATA[<group_notice_item>
	<edittime>1669800836</edittime>
	<datalist count="2">
		<dataitem dataid="ee20cfd986ca7135d3229456cdcb1dff" datatype="8" htmlid="WeNoteHtmlFile">
			<datafmt>.htm</datafmt>
			<fullmd5>8a85dc8dac5591a0231517518e57d9b2</fullmd5>
			<fullsize>656</fullsize>
			<cdn_dataurl>http://wxapp.tc.qq.com/264/20303/stodownload?m=8a85dc8dac5591a0231517518e57d9b2&amp;filekey=30340201010420301e020201080402534804108a85dc8dac5591a0231517518e57d9b202020290040d00000004627466730000000132&amp;hy=SH&amp;storeid=263872386000c05a90c035a230000010800004f4f534817b438b0b6e19d43e&amp;bizid=1023</cdn_dataurl>
			<cdn_datakey>ae1897505cf05694058a7c1a5bd9abe2</cdn_datakey>
		</dataitem>
		<dataitem dataid="be3d1f047954ef83da08b675a3ba893c" datatype="1" htmlid="-1">
			<datadesc>正确答案：
A、给付比例为60%
条款原文：如果被保险人以参加基本医疗保险、公费医疗或政府主办补充医疗的身份投保，但未以参加基本医疗保险、公费医疗或政府主办补充医疗的身份就诊并结算，给付比例为保险单或保险凭证上载明的该被保险人对应的给付比例的 60%。

说人话就是，投保时勾选了“有社保”，就诊时不走医保，全部自费，那给付比例为60%。</datadesc>
		</dataitem>
	</datalist>
	<source sourceid="d3eba20cfc4f64adfe96d0da4e6a7410">
		<fromusr>wstcms</fromusr>
		<tousr>34868845452@chatroom</tousr>
		<sourceid>d3eba20cfc4f64adfe96d0da4e6a7410</sourceid>
	</source>
	<announcement_id>wstcms_34868845452@chatroom_1669800838_920898334</announcement_id>
</group_notice_item>
]]></announcement>
        <textannouncement><![CDATA[正确答案：
A、给付比例为60%
条款原文：如果被保险人以参加基本医疗保险、公费医疗或政府主办补充医疗的身份投保，但未以参加基本医疗保险、公费医疗或政府主办补充医疗的身份就诊并结算，给付比例为保险单或保险凭证上载明的该被保险人对应的给付比例的 60%。

说人话就是，投保时勾选了“有社保”，就诊时不走医保，全部自费，那给付比例为60%。]]></textannouncement>
        <xmlpuretext><![CDATA[0]]></xmlpuretext>
        <announcement_id><![CDATA[wstcms_34868845452@chatroom_1669800838_920898334]]></announcement_id>
    </appmsg>
    <fromusername><![CDATA[wstcms]]></fromusername>
    <appinfo>
        <version>1</version>
        <appname />
    </appinfo>
</msg>
```

输出：'[群公告]'

**对方领取红包**：

```
<img src="SystemMessages_HongbaoIcon.png"/>  陈潇领取了你的<_wc_custom_link_ color="#FD9931" href="weixin://weixinhongbao/opendetail?sendid=1000039801202212157067536925003">红包</_wc_custom_link_>
```

输出：'[对方领取红包]'

**联系人推荐**：

```
<msg username="wxid_lpb1i9tnc44h12" nickname="CYGGL" alias="TTBaoDan999" fullpy="CYGGL" shortpy="CYGGL" imagestatus="3" scene="17" province="上海" city="闵行" sign="逍遥自在迷人可爱??" percard="0" sex="2" certflag="0" certinfo="" certinfoext="" brandIconUrl="" brandHomeUrl="" brandSubscriptConfigUrl="" brandFlags="" regionCode="CN_Shanghai_Minhang"/>
```

输出：'[名片推荐]$nickname'

**对方表情包**：

```
a504159310:0:0:15ca2d96a7595e7cc0fbc481cc967f14::0
```



### 1.2.2 响应规则

* 设置上下文窗口为10条，既当前响应最多参考前面的10条消息
* 将自己发送的连续消息进行合并，以<s>进行连接，这样可以在响应时单次输出多条消息
制作好的数据集后共有13035条数据
最后将数据整理成下面的格式：

```json
{
    "conversation_id": 28367, 
    "category": "Conversation", 
    "conversation": [
        {
            "human": "胡三行:对", 
            "assistant": "乌冬面:好<s>开冲<s>[呲牙]"
        }
    ]
}
```

## 2. SFT

运行脚本sft.sh，使用lora精调chatglm2

训练完成后，可以用测试集看看效果，也可以将模型部署为服务，并邀请好友通过streamlit界面进行交互：

```
bash start_demo.sh
python chatweb.py
```

这里由于训练数据参差不齐的问题（跟每位好友对话习惯不同、没有清洗脏话数据等），会发生一些比较搞笑的对话（**小火龙头像是本人**）：

![image-20231102102539626](https://s2.loli.net/2024/01/22/Mm6os5BgcjPU43C.png)

还有一些比较有意思的回复就不贴了（不太文明），这里再贴一些回复的比较好的例子，例如叫我上号打游戏的：

![image-20231102102904194](https://s2.loli.net/2024/01/22/JkmeqWaU64cvLRx.png)

![image-20231102102931566](https://s2.loli.net/2024/01/22/74d3QhTaDs5AlFp.png)

从SFT结果来看，整体结果还是看得过去的；但实际上，在遇到一些需要结合本人知识回答问题的时候，bot倾向于回答”好的“、”我先睡会“、”[表情包]“这样摸棱两可的回答。这一点似乎是不可避免的，因为我平常也是想到什么说什么，上下文没什么连贯性，可能上文在说勒布朗詹姆斯，下一句就聊到工作了。 

另外的一个问题是，**bot无法一直保持冷静**，特别是朋友们想法设法地让bot爆粗口、或是女朋友设法跟bot吵架的时候。我承认我平时的表达、措辞不那么委婉，但是我不想让这个bot也具有这些缺点。因此，下一步就是利用**RLHF**来使bot的回复变得更文明、更温柔。

## 3. RLHF

由于我只有一张A100可用，所以RLHF阶段用到的4个模型（Reward, Ref, Critic, Policy, 后两个需要参数更新）都打上了LoRA。

### 3.1 Reward Modeling

首先是reward训练数据制作。选择最佳的sft checkpoint，对每个test样例生成3个回复，然后用chatgpt为三个样例打分。chatgpt打分的结果很有可能不正确，需要自己手动调整一下（数据标注十分费时费力，但都是为了效果更好些）。最后将数据制作为下面的形式：

```json
  {
    "source": "驾校周师傅:今天下午一点四十来练车，准时到哈\n乌冬面:科三哈\n驾校周师傅:肯定是的",
    "resp1": "为啥迟到？<s>[尴尬]",
    "resp2": "好<s>[手机图片]<s>我有点疑惑<s>为啥状态是允许的？",
    "resp3": "好<s>[手机图片]<s>收到",
    "scores": [
      "1",
      "2",
      "3"
    ]
  }
```

然后运行train_reward.py，训练reward model

注意reward model的效果对RLHF的影响是非常大的，当然policy model（初始化自sft checkpoint）也是。可以用更多的数据来训练reward model，我这里由于数据标注问题就省掉了，并且policy model也不是很理想，导致RLHF后的模型效果不是很好。

### 3.2 RLHF

运行train_ppo.py。

注意policy model、critic model的底座模型必须是同一个。
