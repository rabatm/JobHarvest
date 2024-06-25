<?php

function get_category_by_name($category_name) {
    $category = get_term_by('name', $category_name, 'hp_listing_category');

    if ($category && !is_wp_error($category)) {
        return $category;
    }

    return null;
}

function create_category_if_not_exists($category_name) {
    $category = get_category_by_name($category_name);

    if (!$category) {
        $category_args = array(
            'taxonomy' => 'hp_listing_category',
            'cat_name' => $category_name,
            'category_description' => '',
            'category_parent' => 0 // Set to 0 for a top-level category
        );

        $category_id = wp_insert_term($category_name, 'hp_listing_category', $category_args);

        if (!is_wp_error($category_id)) {
            return $category_id['term_id'];
        } else {
            return $category_id->get_error_message();
        }
    } else {
        return $category->term_id;
    }
}

function get_post_from($post_title, $post_type) {
    $args = array(
        'post_type' => $post_type,
        's' => $post_title,
        'post_status' => 'publish',
        'posts_per_page' => 1
    );

    $posts = get_posts($args);

    if ($posts) {
        return $posts[0];
    }

    return null;
}

function import_json_data($json_file) {
    if (!check_file_exists($json_file)) {
        return;
    }
    echo "Fichier trouvé: " . $json_file . "<br>";

    $lines = read_file_lines($json_file);
    foreach ($lines as $line) {
        $data = decode_json_line($line);
        if ($data) {
            process_json_data($data);
        }
    }
    //supprimer le fichier
    echo "Suppression du fichier: " . $json_file . "<br>";
    unlink($json_file);
}

function check_file_exists($json_file) {
    if (!file_exists($json_file)) {
        echo "Le fichier n'existe pas.";
        return false;
    }
    return true;
}

function read_file_lines($json_file) {
    $lines = array();
    $handle = fopen($json_file, "r");
    if ($handle) {
        while (($line = fgets($handle)) !== false) {
            $lines[] = $line;
        }
        fclose($handle);
    } else {
        echo "Impossible d'ouvrir le fichier.";
    }
    return $lines;
}

function decode_json_line($line) {
    $data = json_decode($line, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        echo "Erreur de décodage JSON: " . json_last_error_msg() . "<br>";
        return null;
    }
    return $data;
}

function process_json_data($data) {
    $company_id = save_company($data);
    $title_annonces = $data['job_title'] . ' chez ' . $data['company'];
    $job_post = get_post_from($title_annonces, 'hp_listing');
    $job_id = $job_post ? $job_post->ID : null;

    if (!$job_id) {
        $job_id = wp_insert_post(array(
            'post_title' => $title_annonces,
            'post_content' => $data['description'],
            'post_type' => 'hp_listing',
            'post_parent' => $company_id,
            'post_status' => 'publish',
        ));
        
        if (isset($data['salary']) && ($data['salary'] !== 'Not found') && ($data['salary'] !== 'N/A'))
            update_post_meta($job_id, 'hp_salary', $data['salary']);
        if (isset($data['type']) && ($data['type'] !== 'Not found') && ($data['type'] !== 'N/A'))
            update_post_meta($job_id, 'hp_job_type', $data['type']);
        if (isset($data['experience']) && ($data['experience'] !== 'Not found') && ($data['experience'] !== 'N/A'))
            update_post_meta($job_id, 'hp_experience', $data['experience']);
        $city_info = get_city_info_by_name($data['ville']);
        if ($city_info !== null) {
            update_post_meta($job_id, 'hp_location',  $city_info['hp_location']);
            update_post_meta($job_id, 'hp_latitude',  $city_info['hp_latitude']);
            update_post_meta($job_id, 'hp_longitude',  $city_info['hp_longitude']);
        }
        $tags = findTagsInDescription($data['description']);
        if (count($tags) > 0) {
            addTagsToPost($job_id, $tags);
        }
    } else {
        echo "Post already exists: " . $job_id . " - " . $title_annonces . "<br>";
    }

    // Assign category
    $category_id = create_category_if_not_exists($data['categorie']);
    echo "Category ID: " . $category_id . "<br>";

    if (!is_wp_error($category_id)) {
        $taxonomy = 'hp_listing_category';
        $result = wp_set_post_terms($job_id, $category_id, $taxonomy, false);
        if ($result !== false) {
            echo "Category assigned successfully to post ID: " . $job_id . "<br>";
        } else {
            echo "Failed to assign category to post ID: " . $job_id . "<br>";
        }
    } else {
        echo "Error creating category: " . $category_id->get_error_message() . "<br>";
    }
}
