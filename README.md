##关于VLOBSTER网站的说明<br>
        VLOBSTER网站采用Python2.7+flask开发完成，前端采用Bootstrap3，是一个单人/多人的开源博客系统。 
####主要功能：
        文章发布，编辑，管理等；文章标签，二级目录；评论发布，回复，管理等；文章收藏，点赞；用户关注；站内信； 
        图片上传，头像个性化设置；邮箱注册,用户认证,登陆+社交账号登陆；站内文章搜索+全文搜索，站外资源搜索； 
        话题广场；页面边栏支持热门文章，最新访客，日历，标签云等；国际化，语言切换、识别；管理员的后台管理； 
        
####开发工具：
        1.前期后端主要是Ubuntu(15)+Vim；
        2.后期前端开发采用Windows10(64) PowerShell+Notepad++；
        3.浏览器和测试采用Google Chrome和Firefox；
        4.数据库可视化工具SQLitebrowser; 
        5.数据库：sqlite。
        
###如果下载下来试验，遵循以下步骤（Ubuntu）：
        1.安装好python 2.7,激活虚拟环境;
        $sudo apt-get install python 2.7
        $sudo apt-get install python-virtualenv
        $cd vlobster
        $source venv/bin/activate


        2.安装依赖库： 

        $sudo pip install -r requirements.txt 

        3.配置好环境变量：
        FLASKY_MAIL_SENDER = ' '
        FLASKY_ADMIN = ' '
        MAIL_USERNAME = ' '
        MAIL_PASSWORD = ' '
        WTF_CSRF_SECRET_KEY=' '
        SECERT_KEY=' '
        将以上内容保存为.env文件
        如果试验邮件发送功能，还要设置config文件中MAIL_SERVER，MAIL_PORT，MAIL_USE_SSL等变量
   
        4.数据库创建迁移：
        python
        $python manage.py db init
        $python manage.py db migrate -m "versionxxx"
        $python manage.py db upgrade
        

        5.启动前准备:
        建立权限角色,用户账号，测试数据等。

        $python manage.py deploy
        6.运行:

        $python manage.py runserver
        可以访问你的服务器了，但是只能本机访问，如果需要外部计算机访问，可以添加参数:
        $python manage.py runserver --host 0.0.0.0





###如果你只是试用功能，下面是地址和账号：

        试用地址：https://vlobster.herokuapp.com
        普通帐号：abc@vlobster.com     密码：123456
        管理员账号：admin@vlobster.com    密码：admin123

###关于部署过程：
        参照《Flask Web开发 基于Python的Web应用开发实战》,网站部署到Heroku,部署过程一定有个好的VPN，
        作者部署v1.0版本遇到的坑都是网络不佳造成。
        `附注`：部署v2.0版本时也遇到问题，记录如下：
        * 登陆更新代码后，部署数据库时运行```heroku run --app vlobster python manage.py db migrate``` 时
        总是```ConfigParser.NoSectionError: No section: 'alembic'```
            **解决办法：修改.gitignore文件，推送时将migrations文件夹一起推送到git和heroku；
        *问题：```sqlalchemy.exc.CompileError: Postgresql ENUM type requires a name.```
            **解决方法：简单，添加enum名字即可。数据models里用到了Enum数据类型，本地测试没问题，可能Postgresql不兼容。
        Tips:可直接和Git库添加pipeline,直接网站部署升级，比用shell方便太多；只有初始化数据库、产生测试数据不得不用shell
            


###备注说明
        因为作者第一次开发Web应用，在《Flask Web开发 基于Python的Web应用开发实战》基础上参考的同类网站有：
        1."香飘叶子"开发的开源博客"Blog_mini"   http://115.159.72.250:8080/
        2."hulufei"的个人博客 http://www.hulufei.com/
        3."cachalot1984"的个人博客http://hexbot.cn/
        4."fualan1990"的个人博客http://www.fualan.com/
        5."GalaCoding"的开源博客https://github.com/GalaIO/GalaCoding
        6.其他的参考资源可去我个人博客`关于`页面下载
        如果你在部署和使用过程中有疑问，请联系作者：`wzy-511@163.com`

####关于网站未完成内容：
        1.flask-celerey,gunnicorn等支持多进程；
        2.博文的markdown升级采用prism等强大的图文编辑页面。
        3.评论的盖楼（前端）；
        4.增加nginx代理等。
        5.数据库model设计及性能的优化；
        6.部署后上传图片发现上传进度条最好有...
