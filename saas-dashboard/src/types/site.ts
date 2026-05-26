export interface SiteSettings {
  content_strategy: {
    article_type_mix: { review: number; listicle: number };
    always_include_comparison: boolean;
    internal_links_per_post: number;
    language: string;
  };
  publishing_rules: {
    articles_per_day: number;
    delay_between_posts_minutes: number;
    save_as_draft: boolean;
  };
  distribution: {
    publish_to_blog: boolean;
    post_to_facebook: boolean;
    post_to_pinterest: boolean;
    post_to_x: boolean;
  };
}

export const defaultSiteSettings: SiteSettings = {
  content_strategy: {
    article_type_mix: { review: 70, listicle: 30 },
    always_include_comparison: false,
    internal_links_per_post: 2,
    language: 'English',
  },
  publishing_rules: {
    articles_per_day: 5,
    delay_between_posts_minutes: 120,
    save_as_draft: false,
  },
  distribution: {
    publish_to_blog: true,
    post_to_facebook: true,
    post_to_pinterest: false,
    post_to_x: false,
  },
};
