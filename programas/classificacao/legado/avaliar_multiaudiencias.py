import avaliar_claude as runner

if __name__=='__main__':
    runner.DATA=runner.ROOT/'multiaudiencias_v1'
    runner.OUT=runner.ROOT/'claude_multiaudiencias_v1'
    runner.main()
